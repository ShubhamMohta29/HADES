"""Wake word detection: wait_for_wake_word() and listen_for_wake_word_once()."""

import logging
import time
import speech_recognition as sr
from config import WAKE_WORDS_ENV, WAKE_DEBOUNCE
from voice.stt import recognizer

log = logging.getLogger("hades.voice.wake")

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


def wait_for_wake_word():
    """Block until the configured wake word is heard."""
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
    """Open mic briefly; return True if the wake word is heard."""
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
