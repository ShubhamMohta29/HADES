"""Piper TTS: speak(), model init, and audio playback backends."""

import os
import logging
import subprocess
import shutil
import tempfile
import threading
from pathlib import Path
from config import PIPER_MODEL as _CONFIG_PIPER_MODEL

log = logging.getLogger("hades.voice.tts")

VOICES_DIR  = Path(__file__).parent.parent / "voices"
PIPER_MODEL = _CONFIG_PIPER_MODEL or str(VOICES_DIR / "en_GB-alan-medium.onnx")

_PIPER_OK    = False
_piper_voice = None

try:
    from piper import PiperVoice
    _PIPER_API = True
except Exception:
    _PIPER_API = False

try:
    import sounddevice as sd
    import numpy as np
    _AUDIO_OK = True
except Exception:
    _AUDIO_OK = False

_PIPER_MODEL_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    "/en/en_GB/alan/medium/"
)
_PIPER_MODEL_FILES = [
    "en_GB-alan-medium.onnx",
    "en_GB-alan-medium.onnx.json",
]


def _auto_download_piper(model_path: Path):
    import urllib.request
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    for fname in _PIPER_MODEL_FILES:
        dest = VOICES_DIR / fname
        if dest.exists():
            continue
        url = _PIPER_MODEL_URL + fname
        log.info("Downloading Piper voice model: %s", fname)
        print(f"[HADES] Downloading Piper model: {fname}  (first-run, ~60 MB) …")
        try:
            urllib.request.urlretrieve(url, dest)
            log.info("Downloaded %s → %s", fname, dest)
        except Exception as e:
            log.error("Failed to download %s: %s", fname, e)
            print(f"[HADES] WARNING: Could not auto-download {fname}: {e}")
            print(f"        Download manually from: {url}")


def _init_piper() -> bool:
    global _PIPER_OK, _piper_voice
    if _PIPER_OK:
        return True

    model_path = Path(PIPER_MODEL)
    if not model_path.exists():
        if model_path.parent == VOICES_DIR:
            _auto_download_piper(model_path)
        if not model_path.exists():
            log.error(
                "Piper voice model not found at %s. "
                "Download from https://github.com/rhasspy/piper/blob/master/VOICES.md "
                "and place the .onnx + .onnx.json files in ./voices/",
                model_path,
            )
            return False

    if _PIPER_API:
        try:
            _piper_voice = PiperVoice.load(str(model_path))
            _PIPER_OK = True
            log.info("Piper TTS initialized with voice: %s", model_path.name)
            return True
        except Exception as e:
            log.error("Piper API init failed: %s — falling back to CLI", e)

    _local_piper = Path(__file__).parent.parent / "piper" / "piper.exe"
    if _local_piper.exists():
        _local_dir = str(_local_piper.parent)
        if _local_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _local_dir + os.pathsep + os.environ.get("PATH", "")
    if shutil.which("piper"):
        _PIPER_OK = True
        log.info("Piper CLI detected; using subprocess mode")
        return True

    log.error("Neither piper-tts Python package nor piper CLI is available.")
    return False


def _speak_piper_api(text: str):
    if not _AUDIO_OK:
        log.error("sounddevice/numpy not installed — cannot play Piper audio")
        return

    piper_rate = _piper_voice.config.sample_rate
    chunks = []
    for audio_chunk in _piper_voice.synthesize(text):
        if hasattr(audio_chunk, "audio_int16_array"):
            chunks.append(np.array(audio_chunk.audio_int16_array, dtype=np.int16))
        else:
            raw = bytes(audio_chunk)
            if len(raw) % 2:
                raw = raw[:-1]
            chunks.append(np.frombuffer(raw, dtype=np.int16))

    if not chunks:
        return

    audio = np.concatenate(chunks).astype(np.float32) / 32768.0

    try:
        device_rate = int(sd.query_devices(kind="output")["default_samplerate"])
    except Exception:
        device_rate = piper_rate

    if device_rate != piper_rate:
        import math
        ratio   = device_rate / piper_rate
        new_len = math.ceil(len(audio) * ratio)
        audio   = np.interp(
            np.linspace(0, len(audio) - 1, new_len),
            np.arange(len(audio)),
            audio,
        ).astype(np.float32)

    sd.play(audio, samplerate=device_rate, blocking=True)


def _speak_piper_cli(text: str):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        subprocess.run(
            ["piper", "--model", PIPER_MODEL, "--output_file", wav_path],
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
        )
        if _AUDIO_OK:
            import soundfile as sf
            data, sr_ = sf.read(wav_path)
            sd.play(data, sr_, blocking=True)
        else:
            if os.name == "nt":
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
            else:
                subprocess.run(["aplay", wav_path], check=False)
    finally:
        try:
            os.remove(wav_path)
        except OSError:
            pass


_speak_lock = threading.Lock()


def speak(text: str):
    """Say text aloud. Thread-safe; serializes concurrent calls."""
    if not text:
        return
    print("Hades:", text)
    if not _init_piper():
        return
    with _speak_lock:
        try:
            if _PIPER_API and _piper_voice is not None:
                _speak_piper_api(text)
            else:
                _speak_piper_cli(text)
        except Exception as e:
            log.exception("Piper speak failed: %s", e)
