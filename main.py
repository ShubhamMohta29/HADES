import datetime
import webbrowser

from voice import listen, speak
from brain import think

def run():
    speak("Jarvis online.")

    while True:
        user_input = listen()

        if user_input:
            if "exit" in user_input.lower():
                speak("Shutting down.")
                break

            response = think(user_input)
            speak(response)

        if "time" in user_input.lower():
            time = datetime.datetime.now().strftime("%H:%M")
            speak(f"The time is {time}")
            continue

        if "open youtube" in user_input.lower():
            webbrowser.open("https://youtube.com")
            speak("Opening YouTube.")
            continue    

if __name__ == "__main__":
    run()

    