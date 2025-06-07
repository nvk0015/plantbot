#!/usr/bin/env python3
# variants/v1_rule_based/STT/whisper_test.py

import tempfile
import multiprocessing as mp
import collections
import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper
import webrtcvad
import logging

# Start-Methode für Multiprocessing
mp.set_start_method('fork', force=True)

# Logging konfigurieren
template = '%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(level=logging.DEBUG, format=template)
logger = logging.getLogger(__name__)

# VAD-Parameter
VAD_SAMPLE_RATE     = 16000      # arbeitet zuverlässig mit 16 kHz
FRAME_DURATION_MS   = 30         # Frame-Größe (ms)
PADDING_DURATION_MS = 1200        # Pre-/Post-Ringbuffer (ms)
VAD_MODE            = 0          # 0–3, 3 = aggressivster


def list_devices():
    logger.info("Liste verfügbare Audio-Eingabegeräte:")
    for idx, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0:
            logger.info(f"  [{idx}] {dev['name']} @ {dev['default_samplerate']:.0f} Hz")


def record_with_vad(device: int) -> np.ndarray:
    """
    Nimmt Sprache auf bis Ende erkannt per webrtcvad:
    - 16 kHz, mono
    - 30 ms Frames
    - 300 ms Pre-Buffer
    - Stoppt nach 300 ms Non-Speech
    """
    logger.debug(f"Starte VAD-Recording auf Gerät {device}")
    sd.default.device = device
    sd.default.samplerate = VAD_SAMPLE_RATE
    sd.default.channels = 1

    vad = webrtcvad.Vad(VAD_MODE)
    frame_length = int(VAD_SAMPLE_RATE * FRAME_DURATION_MS / 1000)
    padding_frames = int(PADDING_DURATION_MS / FRAME_DURATION_MS)

    ring_buffer = collections.deque(maxlen=padding_frames)
    triggered = False
    voiced_frames = []
    silence_count = 0

    logger.info("Aufnahme bis Ende-Sprache (VAD) erkannt…")
    logger.debug(f"Frame-Länge: {frame_length} Samples, Puffergröße: {padding_frames} Frames")

    frame_index = 0
    while True:
        block = sd.rec(frame_length, dtype='int16')
        sd.wait()
        frame = block.tobytes()

        is_speech = vad.is_speech(frame, VAD_SAMPLE_RATE)
        logger.debug(f"Frame {frame_index}: {'Speech' if is_speech else 'Silence'}")

        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = sum(1 for f, s in ring_buffer if s)
            logger.debug(f"Ringbuffer: {num_voiced}/{ring_buffer.maxlen} voiced")
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                logger.info(f"Sprachbeginn erkannt bei Frame {frame_index}")
                for f, _ in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            voiced_frames.append(frame)
            if not is_speech:
                silence_count += 1
                logger.debug(f"Stille-Count: {silence_count}/{padding_frames}")
                if silence_count > padding_frames:
                    logger.info(f"Sprachende erkannt bei Frame {frame_index}")
                    break
            else:
                if silence_count > 0:
                    logger.debug("Sprache erneut erkannt, Silence-Count zurücksetzen")
                silence_count = 0

        frame_index += 1
    
    # zusammensetzen und zu numpy
    audio_bytes = b''.join(voiced_frames)
    audio = np.frombuffer(audio_bytes, dtype='int16').astype(np.float32) / 32768.0
    duration = len(audio) / VAD_SAMPLE_RATE
    logger.info(f"Aufnahme beendet, Länge: {duration:.2f}s.")
    return audio


def save_wav(audio: np.ndarray, samplerate: int, path: str):
    try:
        sf.write(path, audio, samplerate)
        logger.info(f"WAV gespeichert: {path}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der WAV: {e}")


def _worker_transcribe(model_name: str, audio_path: str, language: str, out_q: mp.Queue):
    try:
        logger.debug(f"Lade Whisper-Modell '{model_name}' im Subprozess")
        model = whisper.load_model(model_name)
        opts = {}
        if language:
            opts["language"] = language
            opts["task"] = "transcribe"
        logger.debug(f"Starte Transkription: {audio_path} mit Optionen {opts}")
        res = model.transcribe(audio_path, **opts)
        text = res["text"].strip()
        logger.info("Transkription abgeschlossen")
        out_q.put(text)
    except Exception as e:
        logger.exception("Fehler in _worker_transcribe")
        out_q.put(None)


def transcribe_with_timeout(model_name: str,
                            audio_path: str,
                            language: str,
                            timeout: int = 15) -> str | None:
    logger.debug(f"Starte Transkriptions-Prozess mit Timeout={timeout}s")
    q = mp.Queue()
    p = mp.Process(target=_worker_transcribe,
                   args=(model_name, audio_path, language, q))
    p.start()
    p.join(timeout)
    if p.is_alive():
        logger.warning("Transkriptions-Prozess läuft zu lange, wird terminiert")
        p.terminate()
        p.join()
        return None
    try:
        result = q.get_nowait()
        logger.debug(f"Erhaltenes Transkript: {result}")
        return result
    except Exception:
        logger.error("Keine Transkript-Daten im Queue gefunden")
        return None


def record_and_transcribe(device_index: int,
                         duration: float,     # CLI-kompatibel, wird ignoriert
                         model_name: str,
                         language: str) -> str:
    """
    Nimmt auf bis Ende-Sprache per VAD, speichert WAV und transkribiert.
    """
    logger.info(f"record_and_transcribe: device={device_index}, model={model_name}, lang={language}")
    audio = record_with_vad(device_index)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        save_wav(audio, VAD_SAMPLE_RATE, tmp.name)
        logger.debug(f"Erstelle temporäre Datei: {tmp.name}")
        logger.info(f"Lade Whisper-Modell '{model_name}' …")
        text = transcribe_with_timeout(model_name, tmp.name, language, timeout=15)
        if not text:
            logger.warning("STT fehlgeschlagen oder Timeout zurückgegeben")
            return "sorry, didnt understand"
        return text

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Whisper STT local mit VAD und Logging")
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--device", type=int, default=None)
    parser.add_argument("--duration", type=float, default=5.0,
                        help="wird ignoriert, da VAD-Recording")
    parser.add_argument("--model", default="tiny")
    parser.add_argument("--lang", default=None)
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
    else:
        dev = args.device if args.device is not None else sd.default.device[0]
        result = record_and_transcribe(dev, args.duration, args.model, args.lang)
        print(result)
