"""Wake word detection: wait_for_wake_word() and listen_for_wake_word_once().

Phase 14: neural path via openwakeword (local ONNX model, no API).
Falls back to STT-based fuzzy matching if openwakeword is not installed
or NEURAL_WAKE_WORD=false is set in .env.
"""

import importlib.util
import logging
import time
import speech_recognition as sr

from config import WAKE_WORDS_ENV, WAKE_DEBOUNCE, WAKE_MODEL, NEURAL_WAKE_WORD
from voice.stt import recognizer

log = logging.getLogger("hades.voice.wake")

# ── Fuzzy STT variants (fallback / NEURAL_WAKE_WORD=false) ───────────────────

_KNOWN_FUZZY: dict = {
    "hades":  ("hades", "ades", "hadez", "hades.", "hey des", "hayes", "hades!"),
    "jarvis": ("jarvis", "jarvis.", "jar vis", "jarvis!", "jar-vis"),
    "friday": ("friday", "frida", "fri day", "friday."),
    "alexa":  ("alexa", "alexia", "alexa."),
}


def _build_wake_set(raw: str) -> frozenset:
    words = [w.strip().lower() for w in raw.split(",") if w.strip()]
    result: set = set()
    for w in words:
        if w in _KNOWN_FUZZY:
            result.update(_KNOWN_FUZZY[w])
        else:
            result.add(w)
            result.add(w + ".")
            result.add(w + "!")
            if w.endswith("s") and len(w) > 3:
                result.add(w[:-1])
    return frozenset(result)


WAKE_WORDS: frozenset = _build_wake_set(WAKE_WORDS_ENV)

_last_wake_time: float = 0.0

# ── Neural model — lazy singleton ─────────────────────────────────────────────

_OWW_AVAILABLE: bool = (
    NEURAL_WAKE_WORD and
    importlib.util.find_spec("openwakeword") is not None
)
_neural_model = None


def _get_neural_model():
    global _neural_model
    if _neural_model is None:
        from openwakeword.model import Model
        models = [WAKE_MODEL] if WAKE_MODEL else []
        log.info("Loading openwakeword model (models=%r)…", models or "all defaults")
        _neural_model = Model(wakeword_models=models, inference_framework="onnx")
        log.info("openwakeword model ready.")
    return _neural_model


# ── Neural implementation (16 kHz raw mic → openwakeword) ────────────────────

def _neural_wait_for_wake_word() -> None:
    global _last_wake_time
    import pyaudio
    import numpy as np

    primary = WAKE_WORDS_ENV.split(",")[0].strip().upper()
    print(f"Waiting for wake word ('{primary}') [neural]…")

    model  = _get_neural_model()
    pa     = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16, channels=1, rate=16000,
        input=True, frames_per_buffer=1280,
    )
    try:
        while True:
            data  = stream.read(1280, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.int16)
            prediction = model.predict(audio)
            for score in prediction.values():
                if score > 0.5:
                    now = time.time()
                    if now - _last_wake_time < WAKE_DEBOUNCE:
                        log.debug("Wake word debounced (%.1fs since last)", now - _last_wake_time)
                        break
                    _last_wake_time = now
                    print("Wake word detected! [neural]")
                    return
    except KeyboardInterrupt:
        raise
    except Exception as e:
        log.warning("Neural wake-word error, falling back to STT: %s", e)
        _stt_wait_for_wake_word()
    finally:
        try:
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception:
            pass


def _neural_listen_once(timeout: int = 3) -> bool:
    global _last_wake_time
    import pyaudio
    import numpy as np

    model    = _get_neural_model()
    pa       = pyaudio.PyAudio()
    stream   = pa.open(
        format=pyaudio.paInt16, channels=1, rate=16000,
        input=True, frames_per_buffer=1280,
    )
    end_time = time.time() + timeout
    try:
        while time.time() < end_time:
            data  = stream.read(1280, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.int16)
            prediction = model.predict(audio)
            for score in prediction.values():
                if score > 0.5:
                    now = time.time()
                    if now - _last_wake_time < WAKE_DEBOUNCE:
                        return False
                    _last_wake_time = now
                    return True
    except KeyboardInterrupt:
        raise
    except Exception as e:
        log.debug("Neural listen-once error: %s", e)
    finally:
        try:
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception:
            pass
    return False


# ── STT fallback implementation ────────────────────────────────────────────────

def _stt_wait_for_wake_word() -> None:
    global _last_wake_time
    primary = WAKE_WORDS_ENV.split(",")[0].strip().upper()
    print(f"Waiting for wake word ('{primary}') [STT]…")
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
                print("Wake word detected! [STT]")
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


def _stt_listen_once(timeout: int = 3) -> bool:
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


# ── Public API — dispatches to neural or STT based on availability ─────────────

def wait_for_wake_word() -> None:
    """Block until the configured wake word is heard."""
    if _OWW_AVAILABLE:
        _neural_wait_for_wake_word()
    else:
        _stt_wait_for_wake_word()


def listen_for_wake_word_once(timeout: int = 3) -> bool:
    """Open mic briefly; return True if the wake word is heard."""
    if _OWW_AVAILABLE:
        return _neural_listen_once(timeout)
    return _stt_listen_once(timeout)
