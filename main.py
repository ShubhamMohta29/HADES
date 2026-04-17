"""HADES main loop + intent router."""

import threading
import re
import logging
import time;
from voice import listen, speak, wait_for_wake_word
from brain import think, clear_memory
from commands import handle_command
from gui import HadesGUI
from config import FACE_AUTH_ENABLED, DEFAULT_CITY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("hades.main")

# ── Lazy imports for optional modules ───────────────────────────────────────
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

# ── Intent patterns ─────────────────────────────────────────────────────────
# Order matters — first match wins.

SCREEN_WORDS = (
    "look at my screen", "what's on my screen", "what is on my screen",
    "analyze my screen", "read my screen", "what do you see",
    "help me with my homework", "solve this on screen",
)

SPOTIFY_WORDS = (
    "play my", "play the", "play some", "pause music", "resume music",
    "stop music", "skip song", "next song", "previous song",
    "what's playing", "what is playing", "shuffle",
)

CRYPTO_COINS = {
    "bitcoin": "bitcoin", "btc": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum",
    "solana": "solana", "sol": "solana",
    "dogecoin": "dogecoin", "doge": "dogecoin",
    "cardano": "cardano", "ada": "cardano",
    "ripple": "ripple", "xrp": "ripple",
}


def route(text, gui):
    t = text.lower()

    # ── Memory reset ────────────────────────────────────────────────────────
    if "clear memory" in t or "forget everything" in t:
        return clear_memory()

    # ── Screen analysis (check BEFORE PC commands so "help me" doesn't collide)
    if any(w in t for w in SCREEN_WORDS):
        from vision import analyze_screen
        return analyze_screen(
            f"The user says: '{text}'. Please help them based on what's on screen."
        )

    # ── Weather ─────────────────────────────────────────────────────────────
    if "weather" in t:
        m = re.search(r"weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)", t)
        city = m.group(1).strip() if m else DEFAULT_CITY
        return _weather(city)

    # ── News ────────────────────────────────────────────────────────────────
    if "news" in t or "headlines" in t:
        m = re.search(r"news\s+(?:about|on)\s+([a-zA-Z\s]+)", t)
        topic = m.group(1).strip() if m else None
        return _news(topic)

    # ── Stocks ──────────────────────────────────────────────────────────────
    if re.search(r"\bstock\b|\bshare price\b", t):
        m = re.search(r"(?:stock|price of|how is)\s+([A-Za-z]{1,6})", t)
        if m:
            return _stock(m.group(1))

    # ── Crypto ──────────────────────────────────────────────────────────────
    for keyword, coin_id in CRYPTO_COINS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", t):
            return _crypto(coin_id)

    # ── Spotify (tighter triggers so it doesn't hijack "play Tesla stock") ──
    if any(w in t for w in SPOTIFY_WORDS):
        result = _spotify(text)
        if result:
            return result

    # ── PC commands (time, volume, apps, notes, etc.) ───────────────────────
    result = handle_command(text)
    if result:
        return result

    # ── Fallback to AI brain ────────────────────────────────────────────────
    gui.set_status("thinking")
    return think(text)


# ── Main voice loop ─────────────────────────────────────────────────────────
def hades_loop(gui):
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
        try:
            gui.set_status("standby")
            wait_for_wake_word()

            gui.set_status("listening")
            time.sleep(0.3)
            speak("Yes, Sir?")
            gui.add_message("Hades", "Yes, Sir?")

            while True:
                gui.set_status("listening")
                user_input = listen()
                if not user_input:
                    continue

                gui.add_message("You", user_input)
                t = user_input.lower()

                if any(w in t for w in ("sleep", "goodbye", "that's all", "stand by")):
                    response = "Standing by, Sir. Call me when you need me."
                    speak(response)
                    gui.add_message("Hades", response)
                    gui.set_status("standby")
                    break

                gui.set_status("thinking")
                response = route(user_input, gui)
                gui.set_status("speaking")
                speak(response)
                gui.add_message("Hades", response)
        except KeyboardInterrupt:
            log.info("Shutting down...")
            return
        except Exception as e:
            log.exception("Error in main loop: %s", e)
            # Don't crash — loop back to standby


# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    gui = HadesGUI()

    def handle_text_command(text):
        try:
            gui.add_message("You", text)
            gui.set_status("thinking")
            response = route(text, gui)
            gui.set_status("speaking")
            speak(response)
            gui.add_message("Hades", response)
            gui.set_status("standby")
        except Exception as e:
            log.exception("Text command error: %s", e)

    gui.on_text_command = handle_text_command

    threading.Thread(target=hades_loop, args=(gui,), daemon=True).start()
    gui.root.mainloop()
