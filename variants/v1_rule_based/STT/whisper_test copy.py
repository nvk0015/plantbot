#!/usr/bin/env python3
# variants/v1_rule_based/STT/whisper_test.py

import os
import tempfile
import multiprocessing as mp
import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper

# Stelle den Start-Methoden-Modus direkt bei Import auf 'fork'
mp.set_start_method('fork', force=True)

# --- Konfig via ENV ---
CHUNK_DURATION   = float(os.getenv("SILENCE_CHUNK", 0.3))
SILENCE_DURATION = float(os.getenv("SILENCE_DUR", 0.8))
SILENCE_TH       = float(os.getenv("SILENCE_TH", 0.01))
MAX_RECORD       = float(os.getenv("MAX_RECORD", 60.0))


def list_devices():
    print("Verfügbare Audio-Eingabegeräte:")
    for idx, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0:
            print(f"  [{idx}] {dev['name']} @ {dev['default_samplerate']:.0f} Hz")


def calibrate_noise(device: int, samplerate: float, seconds: float = 1.0) -> float:
    """
    Nimmt kurz auf, um den Umgebungsgeräusch-Pegel zu bestimmen.
    Gibt RMS als Noise-Floor zurück.
    """
    sd.default.device = device
    sd.default.samplerate = samplerate
    sd.default.channels = 1
    print(f"Kalibriere Noise-Floor ({seconds}s)…")
    block = sd.rec(int(seconds * samplerate), dtype='float32')
    sd.wait()
    rms = np.sqrt(np.mean(np.squeeze(block) ** 2))
    print(f"Noise-Floor RMS: {rms:.6f}")
    return rms


def record_until_silence(device: int,
                         samplerate: float,
                         chunk_duration: float = CHUNK_DURATION,
                         silence_threshold: float = SILENCE_TH,
                         silence_duration: float = SILENCE_DURATION,
                         max_seconds: float = MAX_RECORD) -> np.ndarray:
    """
    Nimmt in Blöcken auf, stoppt bei Stille:
      - Erst wird der Noise-Floor kalibriert
      - Silence-Threshold = max(Static, noise*1.5)
      - Stop, wenn für silence_duration kontinuerlich unter Threshold
      - Oder max_seconds erreicht
    """
    sd.default.device = device
    sd.default.samplerate = samplerate
    sd.default.channels = 1

    # 1) Kalibrierung
    noise_floor = calibrate_noise(device, samplerate)
    threshold = max(silence_threshold, noise_floor * 1.5)
    print(f"Setze Silence-Threshold auf {threshold:.6f}")

    print(f"Aufnahme: bis Stille erkannt "
          f"(chunk={chunk_duration}s, min_silence={silence_duration}s)…")

    chunks = []
    silent_chunks = 0
    needed_silent = int(silence_duration / chunk_duration)
    max_chunks = int(max_seconds / chunk_duration)

    for idx in range(max_chunks):
        block = sd.rec(int(chunk_duration * samplerate), dtype='float32')
        sd.wait()
        block = np.squeeze(block)
        chunks.append(block)

        rms = np.sqrt(np.mean(block**2))
        if rms < threshold:
            silent_chunks += 1
        else:
            silent_chunks = 0

        # Stop-Bedingung: genug stille Blöcke hintereinander
        if silent_chunks >= needed_silent and len(chunks) > needed_silent:
            break

    audio = np.concatenate(chunks)
    total_time = len(audio) / samplerate
    print(f"Aufnahme beendet nach {total_time:.2f}s.")
    return audio


def save_wav(audio: np.ndarray, samplerate: int, path: str):
    sf.write(path, audio, samplerate)
    print(f"WAV gespeichert: {path}")


def _worker_transcribe(model_name: str, audio_path: str, language: str, out_q: mp.Queue):
    try:
        model = whisper.load_model(model_name)
        opts = {}
        if language:
            opts["language"] = language
            opts["task"] = "transcribe"
        res = model.transcribe(audio_path, **opts)
        out_q.put(res["text"].strip())
    except Exception:
        out_q.put(None)


def transcribe_with_timeout(model_name: str,
                            audio_path: str,
                            language: str,
                            timeout: int = 15) -> str | None:
    """
    Führt Whisper-Transkription in Sub-Prozess aus. None bei Fehler/Timeout.
    """
    q = mp.Queue()
    p = mp.Process(target=_worker_transcribe,
                   args=(model_name, audio_path, language, q))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return None
    try:
        return q.get_nowait()
    except mp.queues.Empty:
        return None


def record_and_transcribe(device_index: int,
                          duration: float,      # für CLI-Kompatibilität
                          model_name: str,
                          language: str) -> str:
    """
    Nimmt auf bis Stille, speichert WAV und transkribiert.
    Fehler/Timeout => "sorry, didnt understand".
    """
    info = sd.query_devices(device_index, 'input')
    sr   = info['default_samplerate']

    audio = record_until_silence(device_index, sr)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        save_wav(audio, int(sr), tmp.name)
        print(f"Lade Whisper-Modell '{model_name}' …")
        text = transcribe_with_timeout(model_name, tmp.name, language, timeout=15)
        if not text:
            print("⚠️ STT fehlgeschlagen oder Timeout.")
            return "sorry, didnt understand"
        return text


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Whisper STT local")
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--device", type=int, default=None)
    parser.add_argument("--duration", type=float, default=5.0,
                        help="wird ignoriert, da bis Stille aufgenommen wird")
    parser.add_argument("--model", default="tiny")
    parser.add_argument("--lang", default=None)
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
    else:
        dev = args.device if args.device is not None else sd.default.device[0]
        print(record_and_transcribe(dev, args.duration, args.model, args.lang))
