"""Voice I/O package for HADES — Piper TTS + SpeechRecognition STT + wake word."""

from voice.tts import speak
from voice.stt import listen, MIC_ERROR
from voice.wake import wait_for_wake_word, listen_for_wake_word_once, WAKE_WORDS

__all__ = [
    "speak",
    "listen",
    "MIC_ERROR",
    "wait_for_wake_word",
    "listen_for_wake_word_once",
    "WAKE_WORDS",
]
