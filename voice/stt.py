"""Speech-to-text: listen() and the shared recognizer instance."""

import logging
import speech_recognition as sr

log = logging.getLogger("hades.voice.stt")

recognizer = sr.Recognizer()
recognizer.pause_threshold        = 0.8
recognizer.phrase_threshold       = 0.3
recognizer.non_speaking_duration  = 0.8
recognizer.dynamic_energy_threshold = True
recognizer.energy_threshold       = 300


class _MicUnavailable:
    """Sentinel returned by listen() on OSError — distinct from None (silence)."""
    __slots__ = ()
    def __repr__(self):
        return "MIC_ERROR"


MIC_ERROR = _MicUnavailable()


def listen(timeout: int = 10):
    """Listen once; return transcript str, None (silence/timeout), or MIC_ERROR."""
    try:
        with sr.Microphone() as source:
            print("Listening...")
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
