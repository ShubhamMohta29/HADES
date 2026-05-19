"""Voice I/O for HADES — Piper TTS for speech, SpeechRecognition for input."""

import os
import io
import logging
import subprocess
import shutil
import tempfile
import threading
import time
from pathlib import Path
from config import PIPER_MODEL as _CONFIG_PIPER_MODEL, WAKE_WORDS_ENV, WAKE_DEBOUNCE
import speech_recognition as sr

log = logging.getLogger("hades.voice")

# ── Piper TTS setup ─────────────────────────────────────────────────────────
# Piper is a fast, offline neural TTS. You need:
#   1. pip install piper-tts
#   2. A voice model (.onnx + .onnx.json) — download from:
#      https://github.com/rhasspy/piper/blob/master/VOICES.md
#
# Recommended voices for a JARVIS feel:
#   - en_GB-alan-medium      (British male, calm — most JARVIS-like)
#   - en_GB-northern_english_male-medium
#   - en_US-ryan-high        (US male, deep)
#
# Place the .onnx file in ./voices/ (or set PIPER_MODEL in .env)

VOICES_DIR = Path(__file__).parent / "voices"
PIPER_MODEL = _CONFIG_PIPER_MODEL or str(VOICES_DIR / "en_GB-alan-medium.onnx")

_PIPER_OK = False
_piper_voice = None  # lazy-init piper voice object

try:
    # Prefer the Python API if available (faster — no subprocess per call)
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


def _init_piper():
    """Lazy init of Piper. Returns True if ready."""
    global _PIPER_OK, _piper_voice
    if _PIPER_OK:
        return True

    model_path = Path(PIPER_MODEL)
    if not model_path.exists():
        log.error(
            "Piper voice model not found at %s. "
            "Download one from https://github.com/rhasspy/piper/blob/master/VOICES.md "
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

    # Fallback: look for piper CLI on PATH
    if shutil.which("piper"):
        _PIPER_OK = True
        log.info("Piper CLI detected; using subprocess mode")
        return True

    log.error("Neither piper-tts Python package nor piper CLI is available.")
    return False


def _speak_piper_api(text: str):
    """Synthesize + play audio via Piper Python API + sounddevice."""
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
                raw = raw[:-1]  # drop stray byte to keep int16 alignment
            chunks.append(np.frombuffer(raw, dtype=np.int16))

    if not chunks:
        return

    # Convert to float32 — sounddevice's native type, avoids implicit int16 resampling
    audio = np.concatenate(chunks).astype(np.float32) / 32768.0

    # Resample to the device's native rate if Piper's rate (usually 22050) differs.
    # Mismatched rates cause the driver to interpolate, producing audible stuttering.
    try:
        device_rate = int(sd.query_devices(kind='output')['default_samplerate'])
    except Exception:
        device_rate = piper_rate

    if device_rate != piper_rate:
        import math
        ratio = device_rate / piper_rate
        new_len = math.ceil(len(audio) * ratio)
        audio = np.interp(
            np.linspace(0, len(audio) - 1, new_len),
            np.arange(len(audio)),
            audio,
        ).astype(np.float32)

    sd.play(audio, samplerate=device_rate, blocking=True)


def _speak_piper_cli(text: str):
    """Synthesize + play via piper CLI."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        subprocess.run(
            ["piper", "--model", PIPER_MODEL, "--output_file", wav_path],
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
        )
        # Play the WAV. Try sounddevice first, then OS-native fallbacks.
        if _AUDIO_OK:
            import soundfile as sf
            data, sr_ = sf.read(wav_path)
            sd.play(data, sr_, blocking=True)
        else:
            # Platform fallbacks
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
    """Say text aloud. Thread-safe (serializes concurrent calls)."""
    if not text:
        return
    print("Hades:", text)

    if not _init_piper():
        # Ultimate fallback: just print
        return

    with _speak_lock:
        try:
            if _PIPER_API and _piper_voice is not None:
                _speak_piper_api(text)
            else:
                _speak_piper_cli(text)
        except Exception as e:
            log.exception("Piper speak failed: %s", e)


# ── Speech recognition ──────────────────────────────────────────────────────
recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.8
recognizer.dynamic_energy_threshold = True
recognizer.energy_threshold = 300

# ── Wake word system ─────────────────────────────────────────────────────────
# Known STT mishear variants per word. Google STT is consistent in its mistakes.
_KNOWN_FUZZY: dict = {
    "hades":  ("hades", "ades", "hadez", "hades.", "hey des", "hayes", "hades!"),
    "jarvis": ("jarvis", "jarvis.", "jar vis", "jarvis!", "jar-vis"),
    "friday": ("friday", "frida", "fri day", "friday."),
    "alexa":  ("alexa", "alexia", "alexa."),
}

def _build_wake_set(raw: str) -> frozenset:
    """Build the full set of accepted wake-word strings from the env var."""
    words = [w.strip().lower() for w in raw.split(",") if w.strip()]
    result: set = set()
    for w in words:
        if w in _KNOWN_FUZZY:
            result.update(_KNOWN_FUZZY[w])
        else:
            # Generic rules for unknown words
            result.add(w)
            result.add(w + ".")
            result.add(w + "!")
            # Common mishear: drop trailing 's' (e.g. "hades" → "hade")
            if w.endswith("s") and len(w) > 3:
                result.add(w[:-1])
    return frozenset(result)

WAKE_WORDS: frozenset = _build_wake_set(WAKE_WORDS_ENV)

# ── Debounce state ───────────────────────────────────────────────────────────
_last_wake_time: float = 0.0

# ── Mic error sentinel ───────────────────────────────────────────────────────
class _MicUnavailable:
    """Returned by listen() on OSError — distinct from None (silence/timeout)."""
    __slots__ = ()
    def __repr__(self):
        return "MIC_ERROR"

MIC_ERROR = _MicUnavailable()


def listen(timeout: int = 10):
    """Listen once; return transcript string, None (silence/timeout), or MIC_ERROR (OSError)."""
    try:
        with sr.Microphone() as source:
            print("Listening...")
            # Skip ambient-noise calibration here — dynamic_energy_threshold handles it
            # continuously, and the 0.5s calibration was adding noticeable dead-time
            # at the start of every conversational turn.
            try:
                audio = recognizer.listen(source, timeout=timeout)
            except sr.WaitTimeoutError:
                return None
    except OSError as e:
        log.error("Microphone error: %s", e)
        return MIC_ERROR

    try:
        text = recognizer.recognize_google(audio)
        print("You:", text)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        log.error("Speech API error: %s", e)
        return None
    except Exception as e:
        log.exception("Listen error: %s", e)
        return None


def wait_for_wake_word():
    """Block until user says the wake word (configurable via WAKE_WORDS env var)."""
    global _last_wake_time
    primary = WAKE_WORDS_ENV.split(",")[0].strip().upper()
    print(f"Waiting for wake word ('{primary}')...")
    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            text = recognizer.recognize_google(audio).lower()
            if any(w in text for w in WAKE_WORDS):
                now = time.time()
                if now - _last_wake_time < WAKE_DEBOUNCE:
                    log.debug("Wake word debounced (%.1fs since last)", now - _last_wake_time)
                    continue
                _last_wake_time = now
                print("Wake word detected!")
                return
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except OSError as e:
            log.warning("Mic unavailable in wake-word loop: %s", e)
            time.sleep(3)
            continue
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.debug("wake-word loop: %s", e)
            continue


def listen_for_wake_word_once(timeout: int = 3) -> bool:
    """Open mic briefly and return True if the wake word is heard."""
    global _last_wake_time
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.1)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
        text = recognizer.recognize_google(audio).lower()
        if any(w in text for w in WAKE_WORDS):
            now = time.time()
            if now - _last_wake_time < WAKE_DEBOUNCE:
                return False
            _last_wake_time = now
            return True
        return False
    except (sr.WaitTimeoutError, sr.UnknownValueError, OSError):
        return False
    except KeyboardInterrupt:
        raise
    except Exception as e:
        log.debug("sleep wake-word check: %s", e)
        return False
