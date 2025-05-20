"""
Piper-TTS ➜ Bluetooth-Box (JBL GO 2, Flip 6 …)
Rendert erst komplett, spielt danach blocking ab – dadurch 0 XRUNs / 0 Drop-outs.
"""

from __future__ import annotations
import os, time, logging, threading
from typing import Dict

import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice


# ─────────────────────────── Logging ───────────────────────────
logger = logging.getLogger("tts")
if not logger.handlers:
    logging.basicConfig(
        filename="plant_interface.log",
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
logger.setLevel(logging.DEBUG)


# ─────────────────── Modelle / Voices laden ────────────────────
TTS_DIR = "/home/nvk15697/plants_speak/poc/variants/v1_rule_based/TTS"
MODELS: Dict[str, str] = {
    "en": os.path.join(TTS_DIR, "en_US-amy-low.onnx"),
    # "de": os.path.join(TTS_DIR, "de_DE-karl-medium.onnx"),
}
_CACHE: Dict[str, PiperVoice] = {}


def _get_voice(lang: str) -> PiperVoice:
    key = lang if lang in MODELS else "en"
    if key not in _CACHE:
        pth = MODELS[key]
        logger.debug("Lade Piper-Modell: %s", pth)
        t0 = time.perf_counter()
        _CACHE[key] = PiperVoice.load(pth)
        logger.debug("Modell geladen (%.2f s)", time.perf_counter() - t0)
    return _CACHE[key]


# ────────────────── Wiedergabe-Thread / Serialisierung ──────────────────
_LOCK = threading.Lock()          # keine Überschneidungen


def _play(samples: np.ndarray, sr: int) -> None:
    """Blockiert bis Ende der Wiedergabe, läuft in Background-Thread."""
    try:
        sd.play(samples, sr, blocking=True)
    except Exception:
        logger.exception("Fehler bei sd.play")


# ───────────────────────────── Public API ───────────────────────────────
def speak_text(text: str, lang: str = "en") -> None:
    """Spricht *text* lückenlos über Bluetooth-Lautsprecher."""
    text = text.strip()
    if not text:
        logger.warning("Leerer Text – nichts zu sprechen")
        return

    voice = _get_voice(lang)
    sr = voice.config.sample_rate

    logger.info("TTS-Render (lang=%s, %d Zeichen)", lang, len(text))
    t0 = time.perf_counter()

    # 1) gesamten Text in RAM synthetisieren
    raw = b"".join(voice.synthesize_stream_raw(text))
    samples = np.frombuffer(raw, dtype=np.int16)

    logger.debug("Rendering fertig (%.2f s, %d Frames)",
                 time.perf_counter() - t0, len(samples))

    # 2) in eigenem Thread blocking abspielen (seriell dank Lock)
    def _worker():
        with _LOCK:
            _play(samples, sr)

    threading.Thread(target=_worker, daemon=True).start()
