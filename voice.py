import speech_recognition as sr
import pyttsx3

recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8        # seconds of silence before cutting off
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.8
recognizer.dynamic_energy_threshold = True
recognizer.energy_threshold = 300

def speak(text):
    print("Hades:", text)
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'male' in voice.name.lower() or 'david' in voice.name.lower() or 'mark' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 165)
    engine.setProperty('volume', 1.0)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def listen():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            # No phrase_time_limit = unlimited time to speak
            # pause_threshold controls when it stops after silence
            audio = recognizer.listen(source, timeout=10)
        except sr.WaitTimeoutError:
            return None
    try:
        text = recognizer.recognize_google(audio)
        print("You:", text)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Speech API error: {e}")
        return None
    except Exception as e:
        print(f"Listen error: {e}")
        return None

def wait_for_wake_word():
    print("Waiting for wake word...")
    while True:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                text = recognizer.recognize_google(audio).lower()
                if "hades" in text:
                    print("Wake word detected!")
                    return
            except:
                pass