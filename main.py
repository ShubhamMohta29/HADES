"""HADES main loop + intent router."""

import threading
import re
import logging
import time
from voice import listen, speak, wait_for_wake_word, MIC_ERROR
from brain import think, clear_memory
from commands import handle_command, save_note, get_existing_categories, HELP_HTML
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

NOTE_TRIGGERS = (
    "make a note", "take a note", "note that",
    "add a note", "save a note", "add this note",
)

# Help phrases that should show the command card (exact strip match or regex).
_HELP_PHRASES = frozenset({
    "help", "help me", "commands", "command list",
    "show commands", "list commands", "what can you do",
    "what do you do", "what can i say",
})

# ── Pending multi-turn state ─────────────────────────────────────────────────
# Used for conversational interactions that span two turns (e.g. note category).
_pending_state: dict = {}


def _suggest_category(note_content: str, categories: list) -> str:
    """Quick LLM call to pick the most appropriate category for a note."""
    try:
        from brain import client as _groq, MODEL
        prompt = (
            f"Note: '{note_content}'\n"
            f"Available categories: {', '.join(categories)}\n"
            "Which single category fits best? Reply with only the category name."
        )
        resp = _groq.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0,
        )
        suggested = resp.choices[0].message.content.strip().lower()
        for c in categories:
            if c.lower() in suggested:
                return c
    except Exception as e:
        log.debug("Category suggestion failed: %s", e)
    return categories[0]


def _start_note_flow(note_content: str) -> str:
    """Store the note and ask the user which category to file it under."""
    categories = get_existing_categories()
    suggested = _suggest_category(note_content, categories)
    _pending_state.update({
        "action": "save_note",
        "content": note_content,
        "categories": categories,
        "suggested_category": suggested,
    })
    cats_display = ", ".join(f"'{c}'" for c in categories)
    return (
        f"Which category should I file this under? "
        f"You have: {cats_display}. I suggest '{suggested}', Sir."
    )


_AFFIRM = frozenset({
    "yes", "yeah", "yep", "sure", "ok", "okay", "correct",
    "right", "sounds good", "go ahead", "that", "perfect", "fine",
})
_STOP_WORDS = frozenset({
    "the", "and", "for", "in", "my", "add", "it", "to",
    "put", "under", "please", "file", "save", "note", "a",
})


def _handle_pending_state(t: str) -> str | None:
    """
    Handle the user's response to a pending multi-turn action.
    Returns the response string, or None to fall through to normal routing.
    """
    if _pending_state.get("action") != "save_note":
        _pending_state.clear()
        return None

    categories = _pending_state["categories"]
    suggested  = _pending_state["suggested_category"]

    # 1. User named a known category explicitly
    chosen = next((c for c in categories if c.lower() in t), None)

    # 2. Affirmative response → use suggested
    if not chosen and any(w in t for w in _AFFIRM):
        chosen = suggested

    # 3. Single meaningful word → treat as a new category name
    if not chosen:
        words = [w for w in re.split(r"\W+", t) if len(w) > 2 and w not in _STOP_WORDS]
        if len(words) == 1:
            chosen = words[0]

    if chosen:
        note = _pending_state["content"]
        _pending_state.clear()
        save_note(note, chosen)
        return f"Note saved under '{chosen}', Sir."

    # User response was ambiguous — re-ask once
    cats_str = "' or '".join(categories)
    return f"Sorry, Sir — should I file it under '{cats_str}'? I still suggest '{suggested}'."


def route(text, gui):
    t = text.lower()

    # ── Pending multi-turn state (always checked first) ──────────────────────
    if _pending_state:
        result = _handle_pending_state(t)
        if result is not None:
            return result
        _pending_state.clear()  # unrecognised response — abandon and route normally

    # ── Memory reset ─────────────────────────────────────────────────────────
    if "clear memory" in t or "forget everything" in t:
        return clear_memory()

    # ── Screen analysis (before help — "help me with homework" must hit here) ─
    if any(w in t for w in SCREEN_WORDS):
        from vision import analyze_screen
        return analyze_screen(
            f"The user says: '{text}'. Please help them based on what's on screen."
        )

    # ── Help command ──────────────────────────────────────────────────────────
    if t.strip() in _HELP_PHRASES or re.search(r"^(show|list|what).*(command|capability)", t):
        gui.add_help_card(HELP_HTML)
        return "Here is a list of things I can help you with, Sir."

    # ── Note taking (conversational — must come before handle_command) ────────
    if any(trigger in t for trigger in NOTE_TRIGGERS):
        note = re.sub(
            r".*(note that|make a note|take a note|add a note|save a note|add this note)[:\s]*",
            "", t,
        ).strip()
        if note:
            return _start_note_flow(note)

    # ── Weather ──────────────────────────────────────────────────────────────
    if "weather" in t:
        m = re.search(r"weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)", t)
        city = m.group(1).strip() if m else DEFAULT_CITY
        return _weather(city)

    # ── News ─────────────────────────────────────────────────────────────────
    if "news" in t or "headlines" in t:
        m = re.search(r"news\s+(?:about|on)\s+([a-zA-Z\s]+)", t)
        topic = m.group(1).strip() if m else None
        return _news(topic)

    # ── Stocks ───────────────────────────────────────────────────────────────
    if re.search(r"\bstock\b|\bshare price\b", t):
        # Handle both "Tesla stock" and "stock Tesla" / "price of Tesla" orders
        m = re.search(r"([A-Za-z]{1,6})\s+(?:stock|share)", t) or \
            re.search(r"(?:stock|price of|how is)\s+([A-Za-z]{1,6})", t)
        if m:
            return _stock(m.group(1))

    # ── Crypto ───────────────────────────────────────────────────────────────
    for keyword, coin_id in CRYPTO_COINS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", t):
            return _crypto(coin_id)

    # ── Spotify (tighter triggers so it doesn't hijack "play Tesla stock") ───
    if any(w in t for w in SPOTIFY_WORDS):
        result = _spotify(text)
        if result:
            return result

    # ── PC commands (time, volume, apps, notes read, etc.) ───────────────────
    result = handle_command(text)
    if result:
        return result

    # ── Fallback to AI brain ──────────────────────────────────────────────────
    gui.set_status("thinking")
    return think(text)


# Words that trigger sleep mode. Include STT spacing variants.
SLEEP_WORDS = (
    "sleep", "goodbye", "good bye", "goodnight", "good night",
    "that's all", "stand by", "standby", "go to sleep",
)


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

    _sleeping = False  # distinguishes user-triggered sleep from initial standby

    while True:
        try:
            # Set the correct idle status BEFORE blocking on the wake word.
            # This ensures the GUI reflects the state while the mic is listening.
            if _sleeping:
                gui.set_status("sleeping")
            else:
                gui.set_status("standby")

            wait_for_wake_word()  # mic stays open; ignores everything except "HADES"

            if _sleeping:
                _sleeping = False
                gui.set_status("listening")
                time.sleep(0.3)
                speak("I'm back, Sir. What do you need?")
                gui.add_message("Hades", "I'm back, Sir. What do you need?")
            else:
                gui.set_status("listening")
                time.sleep(0.3)
                speak("Yes, Sir?")
                gui.add_message("Hades", "Yes, Sir?")

            _mic_err_streak = 0
            while True:
                gui.set_status("listening")
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
                    continue

                gui.add_message("You", user_input)
                t = user_input.lower()

                if any(w in t for w in SLEEP_WORDS):
                    _pending_state.clear()  # abandon any in-progress action
                    response = "Going to sleep, Sir. Call me when you need me."
                    speak(response)
                    gui.add_message("Hades", response)
                    _sleeping = True
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
            _sleeping = False  # reset on unexpected error so standby shows next


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
