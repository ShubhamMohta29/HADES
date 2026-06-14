"""Intent router — maps user text to the right handler and manages multi-turn state."""

import re
import logging

from brain import think, clear_memory
from commands import (
    handle_command,
    save_note,
    get_existing_categories,
    delete_last_note,
    delete_notes,
    HELP_HTML,
)
from config import DEFAULT_CITY

log = logging.getLogger("hades.router")

# ── Intent keyword sets ──────────────────────────────────────────────────────

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

CRYPTO_COINS: dict[str, str] = {
    "bitcoin":  "bitcoin", "btc":      "bitcoin",
    "ethereum": "ethereum", "eth":     "ethereum",
    "solana":   "solana",  "sol":      "solana",
    "dogecoin": "dogecoin", "doge":    "dogecoin",
    "cardano":  "cardano",  "ada":     "cardano",
    "ripple":   "ripple",   "xrp":     "ripple",
}

NOTE_TRIGGERS = (
    "make a note", "take a note", "note that",
    "add a note", "save a note", "add this note",
)

_HELP_PHRASES = frozenset({
    "help", "help me", "commands", "command list",
    "show commands", "list commands", "what can you do",
    "what do you do", "what can i say",
})

# ── Service shims (lazy imports keep startup fast and Spotify auth deferred) ──

def _weather(city: str) -> str:
    from services.weather import get_weather
    return get_weather(city)

def _news(topic=None) -> str:
    from services.news import get_news
    return get_news(topic)

def _stock(symbol: str) -> str:
    from services.stocks import get_stock
    return get_stock(symbol)

def _crypto(coin_id: str) -> str:
    from services.stocks import get_crypto
    return get_crypto(coin_id)

def _spotify(text: str):
    from services.spotify import spotify_command
    return spotify_command(text)

# ── Multi-turn pending state ─────────────────────────────────────────────────

_pending_state: dict = {}

_AFFIRM = frozenset({
    "yes", "yeah", "yep", "sure", "ok", "okay", "correct",
    "right", "sounds good", "go ahead", "that", "perfect", "fine",
})
_STOP_WORDS = frozenset({
    "the", "and", "for", "in", "my", "add", "it", "to",
    "put", "under", "please", "file", "save", "note", "a",
})


def _suggest_category(note_content: str, categories: list) -> str:
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


def _start_note_flow(note_content: str, user_id: str = None) -> str:
    categories = get_existing_categories(user_id)
    suggested  = _suggest_category(note_content, categories)
    _pending_state.update({
        "action":             "save_note",
        "content":            note_content,
        "categories":         categories,
        "suggested_category": suggested,
        "user_id":            user_id,
    })
    cats_display = ", ".join(f"'{c}'" for c in categories)
    return (f"Which category should I file this under? "
            f"You have: {cats_display}. I suggest '{suggested}', Sir.")


def _handle_pending_state(t: str) -> str | None:
    if _pending_state.get("action") != "save_note":
        _pending_state.clear()
        return None

    categories = _pending_state["categories"]
    suggested  = _pending_state["suggested_category"]
    user_id    = _pending_state.get("user_id")

    chosen = next((c for c in categories if c.lower() in t), None)

    if not chosen and any(w in t for w in _AFFIRM):
        chosen = suggested

    if not chosen:
        words = [w for w in re.split(r"\W+", t) if len(w) > 2 and w not in _STOP_WORDS]
        if len(words) == 1:
            chosen = words[0]

    if chosen:
        note = _pending_state["content"]
        _pending_state.clear()
        save_note(note, chosen, user_id=user_id)
        return f"Note saved under '{chosen}', Sir."

    cats_str = "' or '".join(categories)
    return f"Sorry, Sir — should I file it under '{cats_str}'? I still suggest '{suggested}'."


# ── Main router ──────────────────────────────────────────────────────────────

def route(text: str, gui, user_id: str = None) -> str:
    t = text.lower()

    if _pending_state:
        result = _handle_pending_state(t)
        if result is not None:
            return result
        _pending_state.clear()

    if "clear memory" in t or "forget everything" in t:
        return clear_memory(user_id)

    if any(w in t for w in SCREEN_WORDS):
        from vision import analyze_screen
        return analyze_screen(
            f"Describe what you see in the attached screenshot and help the user with their request: '{text}'."
        )

    if t.strip() in _HELP_PHRASES or re.search(r"^(show|list|what).*(command|capability)", t):
        gui.add_help_card(HELP_HTML)
        return "Here is a list of things I can help you with, Sir."

    if re.search(r"\bdelete\b.+\blast\b.+\bnote\b|\bdelete\b.+\bnote\b.+\blast\b", t):
        return delete_last_note(user_id=user_id)
    _del_cat = re.search(r"\bdelete\b.+?\b(my\s+)?(\w+)\s+notes?\b", t)
    if _del_cat:
        _cat = _del_cat.group(2)
        if _cat not in {"all", "my", "the", "a"}:
            return delete_notes(_cat, user_id=user_id)
        return delete_notes(user_id=user_id)
    if re.search(r"\bdelete\b.+\ball\b.+\bnotes?\b|\bdelete\b.+\bnotes?\b.+\ball\b", t):
        return delete_notes(user_id=user_id)

    if any(trigger in t for trigger in NOTE_TRIGGERS):
        note = re.sub(
            r".*(note that|make a note|take a note|add a note|save a note|add this note)[:\s]*",
            "", t,
        ).strip()
        if note:
            return _start_note_flow(note, user_id)

    if "weather" in t:
        m    = re.search(r"weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)", t)
        city = m.group(1).strip() if m else DEFAULT_CITY
        return _weather(city)

    if "news" in t or "headlines" in t:
        m     = re.search(r"news\s+(?:about|on)\s+([a-zA-Z\s]+)", t)
        topic = m.group(1).strip() if m else None
        return _news(topic)

    if re.search(r"\bstock\b|\bshare price\b", t):
        m = (re.search(r"([A-Za-z]{1,6})\s+(?:stock|share)", t) or
             re.search(r"(?:stock|price of|how is)\s+([A-Za-z]{1,6})", t))
        if m:
            return _stock(m.group(1))

    for keyword, coin_id in CRYPTO_COINS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", t):
            return _crypto(coin_id)

    if any(w in t for w in SPOTIFY_WORDS):
        result = _spotify(text)
        if result:
            return result

    result = handle_command(text)
    if result:
        return result

    gui.set_status("thinking")
    return think(text, user_id=user_id)
