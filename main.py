"""This is the main class which runs the HADES assistant,
handling the main loop, routing commands,
and integrating all components together."""

import threading
import re
import datetime

from voice import listen, speak, wait_for_wake_word
from brain import think, clear_memory
from commands import handle_command
from gui import HadesGUI
from config import FACE_AUTH_ENABLED, DEFAULT_CITY

# Lazy imports for optional modules
def _weather(city):
    from weather import get_weather
    return get_weather(city)

def _news(topic=None):
    from news import get_news
    return get_news(topic)

def _stock(symbol):
    from stocks import get_stock
    return get_stock(symbol)

def _crypto(symbol):
    from stocks import get_crypto
    return get_crypto(symbol)

def _spotify(text):
    from spotify import spotify_command
    return spotify_command(text)

# Smart intent router
def route(text, gui):
    t = text.lower()

    # Memory
    if "clear memory" in t or "forget everything" in t:
        return clear_memory()

    # Weather
    if "weather" in t:
        match = re.search(r'weather (?:in|for|at) ([a-zA-Z\s]+)', t)
        city = match.group(1).strip() if match else DEFAULT_CITY
        return _weather(city)

    # News
    if "news" in t or "headlines" in t:
        match = re.search(r'news (?:about|on) ([a-zA-Z\s]+)', t)
        topic = match.group(1).strip() if match else None
        return _news(topic)

    # Stocks
    if "stock" in t:
        match = re.search(r'(?:stock|price of|how is)\s+([A-Za-z]+)', t)
        symbol = match.group(1) if match else None
        if symbol:
            return _stock(symbol)

    # ── Crypto ──────────────────────────────────────────────────────────────
    if any(c in t for c in ["bitcoin", "ethereum", "crypto", "btc", "eth"]):
        coins = {"bitcoin": "bitcoin", "btc": "bitcoin",
                 "ethereum": "ethereum", "eth": "ethereum",
                 "crypto": "bitcoin"}
        for keyword, coin_id in coins.items():
            if keyword in t:
                return _crypto(coin_id)

    # Spotify
    if any(w in t for w in ["play", "pause", "skip", "next song", "previous song",
                             "what's playing", "shuffle", "resume music", "stop music"]):
        result = _spotify(text)
        if result:
            return result

    # PC commands
    result = handle_command(text)
    if result:
        return result
    
    # Screen analysis
    if any(w in t for w in ["look at my screen", "what's on my screen", 
                        "help me with this", "what do you see",
                        "analyze my screen", "read my screen",
                        "help me with my homework", "solve this"]):
        from vision import analyze_screen
        # Use whatever the user said as the prompt for more context
        response = analyze_screen(f"The user says: '{text}'. Please help them based on what you see on screen.")
        return response

    # Fallback to AI
    gui.set_status("thinking")
    return think(text)

# Main loop
def hades_loop(gui):
    # Optional face auth on startup
    if FACE_AUTH_ENABLED:
        gui.add_system_message("Face verification required...")
        from face_auth import verify_face
        if verify_face():
            gui.add_system_message("Identity confirmed. Welcome, Sir.")
            speak("Identity confirmed. Welcome back, Sir.")
        else:
            gui.add_system_message("Face not recognized. Access denied.")
            speak("I don't recognize you, Sir. Access denied.")
            return

    speak("Hades online. All systems nominal. Say my name to activate.")
    gui.add_system_message("All systems nominal. Waiting for activation.")

    while True:
        gui.set_status("standby")
        wait_for_wake_word()

        gui.set_status("listening")
        speak("Yes, Sir?")
        gui.add_message("Hades", "Yes, Sir?")

        # Stay active until sleep command
        while True:
            gui.set_status("listening")
            user_input = listen()

            if not user_input:
                continue

            gui.add_message("You", user_input)
            t = user_input.lower()

            # Sleep / deactivate
            if any(w in t for w in ["sleep", "goodbye", "that's all", "stand by"]):
                response = "Standing by, Sir. Call me when you need me."
                speak(response)
                gui.add_message("Hades", response)
                gui.set_status("standby")
                break

            # Route and respond
            gui.set_status("thinking")
            response = route(user_input, gui)

            gui.set_status("speaking")
            speak(response)
            gui.add_message("Hades", response)

# Entry point
if __name__ == "__main__":
    gui = HadesGUI()

    # Handle text input from GUI
    def handle_text_command(text):
        gui.add_message("You", text)
        gui.set_status("thinking")
        response = route(text, gui)
        gui.set_status("speaking")
        speak(response)
        gui.add_message("Hades", response)
        gui.set_status("standby")

    gui.on_text_command = handle_text_command  # connect callback

    threading.Thread(target=hades_loop, args=(gui,), daemon=True).start()
    gui.root.mainloop()