"""HADES entry point — main voice loop and startup wiring."""

import threading
import logging
import time

from voice import listen, speak, wait_for_wake_word, MIC_ERROR
from router import route, _pending_state
from gui import HadesGUI
from config import FACE_AUTH_ENABLED, FOLLOWUP_TIMEOUT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("hades.main")

SLEEP_WORDS = (
    "sleep", "goodbye", "good bye", "goodnight", "good night",
    "that's all", "stand by", "standby", "go to sleep",
)


def hades_loop(gui, user_id: str = None):
    if FACE_AUTH_ENABLED:
        gui.add_system_message("Face verification required...")
        from face_auth import verify_face
        if verify_face(user_id=user_id):
            gui.add_system_message("Identity confirmed. Welcome, Sir.")
            speak("Identity confirmed. Welcome back, Sir.")
        else:
            gui.add_system_message("Face not recognized. Access denied.")
            speak("I don't recognize you, Sir. Access denied.")
            return

    speak("Hades online. All systems nominal. Say my name to activate.")
    gui.add_system_message("All systems nominal. Waiting for activation.")

    _sleeping = False

    while True:
        try:
            gui.set_status("sleeping" if _sleeping else "standby")
            wait_for_wake_word()

            if _sleeping:
                _sleeping = False
                gui.set_status("listening")
                speak("I'm back, Sir. What do you need?")
                gui.add_message("Hades", "I'm back, Sir. What do you need?")
            else:
                gui.set_status("listening")
                speak("Yes, Sir?")
                gui.add_message("Hades", "Yes, Sir?")

            _mic_err_streak = 0
            _in_followup = False
            _followup_silence_start = 0.0

            while True:
                gui.set_status("followup" if _in_followup else "listening")
                user_input = listen()

                if user_input is MIC_ERROR:
                    _mic_err_streak += 1
                    if _mic_err_streak == 3:
                        gui.add_system_message(
                            "Microphone unavailable — use the text input, Sir."
                        )
                    time.sleep(2)
                    continue

                if _mic_err_streak >= 3:
                    gui.add_system_message("Microphone reconnected.")
                _mic_err_streak = 0

                if not user_input:
                    if _in_followup and time.time() - _followup_silence_start > FOLLOWUP_TIMEOUT:
                        _in_followup = False
                        gui.add_system_message("Follow-up window closed. Say my name to activate.")
                        break
                    continue

                _in_followup = False
                gui.add_message("You", user_input)

                if any(w in user_input.lower() for w in SLEEP_WORDS):
                    _pending_state.clear()
                    response = "Going to sleep, Sir. Call me when you need me."
                    speak(response)
                    gui.add_message("Hades", response)
                    _sleeping = True
                    break

                gui.set_status("thinking")
                response = route(user_input, gui, user_id=user_id)
                gui.set_status("speaking")
                speak(response)
                gui.add_message("Hades", response)

                _in_followup = True
                _followup_silence_start = time.time()

        except KeyboardInterrupt:
            log.info("Shutting down...")
            return
        except Exception as e:
            log.exception("Error in main loop: %s", e)
            _sleeping = False


if __name__ == "__main__":
    gui = HadesGUI()

    _user_id    = [None]
    _auth_event = threading.Event()

    def _on_auth_complete(uid: str | None):
        _user_id[0] = uid
        _auth_event.set()
        msg = "Authenticated. Session active." if uid else "Running in local mode."
        gui.add_system_message(msg)

    gui.on_auth_complete = _on_auth_complete

    _text_state = {"sleeping": False}

    def handle_text_command(text: str):
        try:
            gui.add_message("You", text)
            t = text.lower()

            if _text_state["sleeping"]:
                _text_state["sleeping"] = False
                gui.set_status("standby")

            if any(w in t for w in SLEEP_WORDS):
                _pending_state.clear()
                response = "Shutting down, Sir. Goodnight."
                gui.set_status("sleeping")
                speak(response)
                gui.add_message("Hades", response)
                _text_state["sleeping"] = True
                return

            gui.set_status("thinking")
            response = route(text, gui, user_id=_user_id[0])
            gui.set_status("speaking")
            speak(response)
            gui.add_message("Hades", response)
            gui.set_status("standby")
        except Exception as e:
            log.exception("Text command error: %s", e)

    gui.on_text_command = handle_text_command

    def _start_after_auth():
        _auth_event.wait()
        hades_loop(gui, user_id=_user_id[0])

    threading.Thread(target=_start_after_auth, daemon=True).start()
    gui.root.mainloop()
