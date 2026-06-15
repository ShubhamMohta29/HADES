"""Intent router — maps user text to the right handler via the Strategy pattern.

Each intent is a separate _Handler subclass implementing can_handle / handle.
To add a new intent: create a subclass, append an instance to _HANDLERS.
route() itself never needs to change (Open/Closed Principle).
"""

import re
import time
import functools
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
from config import DEFAULT_CITY, CONFIRM_TIMEOUT

log = logging.getLogger("hades.router")

# ── Keyword sets ──────────────────────────────────────────────────────────────

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

# ── Service shims (lazy imports; Spotify OAuth deferred until first use) ───────

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

# ── Multi-turn pending state (note category flow) ─────────────────────────────

_pending_state: dict = {}

_AFFIRM = frozenset({
    "yes", "yeah", "yep", "sure", "ok", "okay", "correct",
    "right", "sounds good", "go ahead", "that", "perfect", "fine",
})
_STOP_WORDS = frozenset({
    "the", "and", "for", "in", "my", "add", "it", "to",
    "put", "under", "please", "file", "save", "note", "a",
})

# Confirm / deny keywords for the action confirmation gate (Phase 16)
_CONFIRM_WORDS = frozenset({
    "yes", "yeah", "yep", "confirm", "do it", "go ahead",
    "proceed", "sure", "affirmative",
})
_DENY_WORDS = frozenset({
    "no", "nope", "cancel", "stop", "abort", "never mind",
    "nevermind", "don't", "dont",
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


def _handle_confirm_state(lower: str) -> str:
    """Handle a pending confirm_action — yes executes, no cancels, timeout auto-cancels."""
    if time.time() - _pending_state.get("set_at", 0) > CONFIRM_TIMEOUT:
        _pending_state.clear()
        return "Confirmation timed out. Action cancelled, Sir."
    if any(w in lower for w in _CONFIRM_WORDS):
        fn   = _pending_state["callable"]
        _pending_state.clear()
        return fn() or "Done, Sir."
    if any(w in lower for w in _DENY_WORDS):
        _pending_state.clear()
        return "Cancelled, Sir."
    desc = _pending_state["description"]
    return f"Please confirm — {desc}? Say 'yes' to proceed or 'no' to cancel, Sir."


def _handle_pending_state(lower: str) -> str | None:
    action = _pending_state.get("action")

    if action == "confirm_action":
        return _handle_confirm_state(lower)

    if action != "save_note":
        _pending_state.clear()
        return None

    categories = _pending_state["categories"]
    suggested  = _pending_state["suggested_category"]
    user_id    = _pending_state.get("user_id")

    chosen = next((c for c in categories if c.lower() in lower), None)

    if not chosen and any(w in lower for w in _AFFIRM):
        chosen = suggested

    if not chosen:
        words = [w for w in re.split(r"\W+", lower) if len(w) > 2 and w not in _STOP_WORDS]
        if len(words) == 1:
            chosen = words[0]

    if chosen:
        note = _pending_state["content"]
        _pending_state.clear()
        save_note(note, chosen, user_id=user_id)
        return f"Note saved under '{chosen}', Sir."

    cats_str = "' or '".join(categories)
    return f"Sorry, Sir — should I file it under '{cats_str}'? I still suggest '{suggested}'."


# ── Strategy base class ───────────────────────────────────────────────────────

class _Handler:
    """Base for intent handlers. Subclass, override can_handle + handle, register in _HANDLERS."""
    def can_handle(self, text: str, lower: str) -> bool:
        raise NotImplementedError
    def handle(self, text: str, lower: str, gui, user_id: str | None) -> str | None:
        raise NotImplementedError


# ── Concrete intent handlers (one class = one responsibility) ─────────────────

class _ClearMemoryHandler(_Handler):
    def can_handle(self, text, lower):
        return "clear memory" in lower or "forget everything" in lower
    def handle(self, text, lower, gui, user_id):
        return clear_memory(user_id)


class _ScreenHandler(_Handler):
    def can_handle(self, text, lower):
        return any(w in lower for w in SCREEN_WORDS)
    def handle(self, text, lower, gui, user_id):
        from vision import analyze_screen
        return analyze_screen(
            f"Describe what you see in the attached screenshot and help the user with their request: '{text}'."
        )


class _HelpHandler(_Handler):
    def can_handle(self, text, lower):
        return (lower.strip() in _HELP_PHRASES or
                bool(re.search(r"^(show|list|what).*(command|capability)", lower)))
    def handle(self, text, lower, gui, user_id):
        gui.add_help_card(HELP_HTML)
        return "Here is a list of things I can help you with, Sir."


class _DeleteNoteHandler(_Handler):
    _LAST  = re.compile(r"\bdelete\b.+\blast\b.+\bnote\b|\bdelete\b.+\bnote\b.+\blast\b")
    _CAT   = re.compile(r"\bdelete\b.+?\b(my\s+)?(\w+)\s+notes?\b")
    _ALL   = re.compile(r"\bdelete\b.+\ball\b.+\bnotes?\b|\bdelete\b.+\bnotes?\b.+\ball\b")

    def can_handle(self, text, lower):
        return "delete" in lower and "note" in lower

    def handle(self, text, lower, gui, user_id):
        if self._LAST.search(lower):
            return delete_last_note(user_id=user_id)
        if self._ALL.search(lower):
            _uid = user_id
            _pending_state.update({
                "action":      "confirm_action",
                "callable":    functools.partial(delete_notes, user_id=_uid),
                "description": "delete all your notes",
                "set_at":      time.time(),
            })
            return "Are you sure you want to delete all your notes, Sir? This cannot be undone."
        m = self._CAT.search(lower)
        if m:
            cat = m.group(2)
            if cat not in {"all", "my", "the", "a"}:
                _uid = user_id
                _pending_state.update({
                    "action":      "confirm_action",
                    "callable":    functools.partial(delete_notes, cat, user_id=_uid),
                    "description": f"delete all your {cat} notes",
                    "set_at":      time.time(),
                })
                return f"Are you sure you want to delete all your {cat} notes, Sir?"
            _uid = user_id
            _pending_state.update({
                "action":      "confirm_action",
                "callable":    functools.partial(delete_notes, user_id=_uid),
                "description": "delete all your notes",
                "set_at":      time.time(),
            })
            return "Are you sure you want to delete all your notes, Sir? This cannot be undone."
        return None


class _NoteHandler(_Handler):
    _STRIP = re.compile(
        r".*(note that|make a note|take a note|add a note|save a note|add this note)[:\s]*"
    )
    def can_handle(self, text, lower):
        return any(trigger in lower for trigger in NOTE_TRIGGERS)
    def handle(self, text, lower, gui, user_id):
        note = self._STRIP.sub("", lower).strip()
        return _start_note_flow(note, user_id) if note else None


class _WeatherHandler(_Handler):
    def can_handle(self, text, lower):
        return "weather" in lower
    def handle(self, text, lower, gui, user_id):
        m    = re.search(r"weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)", lower)
        city = m.group(1).strip() if m else DEFAULT_CITY
        return _weather(city)


class _NewsHandler(_Handler):
    def can_handle(self, text, lower):
        return "news" in lower or "headlines" in lower
    def handle(self, text, lower, gui, user_id):
        m     = re.search(r"news\s+(?:about|on)\s+([a-zA-Z\s]+)", lower)
        topic = m.group(1).strip() if m else None
        return _news(topic)


class _StockHandler(_Handler):
    _PATTERN = re.compile(r"\bstock\b|\bshare price\b")
    def can_handle(self, text, lower):
        return bool(self._PATTERN.search(lower))
    def handle(self, text, lower, gui, user_id):
        m = (re.search(r"([A-Za-z]{1,6})\s+(?:stock|share)", lower) or
             re.search(r"(?:stock|price of|how is)\s+([A-Za-z]{1,6})", lower))
        return _stock(m.group(1)) if m else None


class _CryptoHandler(_Handler):
    def can_handle(self, text, lower):
        return any(re.search(rf"\b{re.escape(k)}\b", lower) for k in CRYPTO_COINS)
    def handle(self, text, lower, gui, user_id):
        for keyword, coin_id in CRYPTO_COINS.items():
            if re.search(rf"\b{re.escape(keyword)}\b", lower):
                return _crypto(coin_id)
        return None


class _SpotifyHandler(_Handler):
    def can_handle(self, text, lower):
        return any(w in lower for w in SPOTIFY_WORDS)
    def handle(self, text, lower, gui, user_id):
        return _spotify(text) or None


class _PowerConfirmHandler(_Handler):
    """Intercept destructive power commands (shutdown/restart) and require confirmation."""
    _SHUTDOWN = re.compile(r"\bshutdown\b|\bshut\s+down\b")
    _RESTART  = re.compile(r"\brestart\b")

    def can_handle(self, text, lower):
        if "cancel" in lower:
            return False
        return bool(self._SHUTDOWN.search(lower)) or bool(self._RESTART.search(lower))

    def handle(self, text, lower, gui, user_id):
        if self._SHUTDOWN.search(lower):
            desc = "shut down the computer"
        elif self._RESTART.search(lower):
            desc = "restart the computer"
        else:
            return None
        _pending_state.update({
            "action":      "confirm_action",
            "callable":    functools.partial(handle_command, text),
            "description": desc,
            "set_at":      time.time(),
        })
        return f"Are you sure you want to {desc}, Sir?"


class _PCCommandHandler(_Handler):
    def can_handle(self, text, lower):
        return True
    def handle(self, text, lower, gui, user_id):
        return handle_command(text) or None


class _BrainFallback(_Handler):
    def handle(self, text, lower, gui, user_id):
        gui.set_status("thinking")
        return think(text, user_id=user_id)


# ── Handler registry — position defines priority ───────────────────────────────

_HANDLERS: list[_Handler] = [
    _ClearMemoryHandler(),
    _ScreenHandler(),
    _HelpHandler(),
    _DeleteNoteHandler(),
    _NoteHandler(),
    _WeatherHandler(),
    _NewsHandler(),
    _StockHandler(),
    _CryptoHandler(),
    _SpotifyHandler(),
    _PowerConfirmHandler(),
    _PCCommandHandler(),
]

_FALLBACK = _BrainFallback()


# ── Dispatcher ────────────────────────────────────────────────────────────────

def route(text: str, gui, user_id: str = None) -> str:
    """Dispatch user text to the first matching handler; fall back to the LLM."""
    lower = text.lower()

    if _pending_state:
        result = _handle_pending_state(lower)
        if result is not None:
            return result
        _pending_state.clear()

    for handler in _HANDLERS:
        if handler.can_handle(text, lower):
            result = handler.handle(text, lower, gui, user_id)
            if result is not None:
                return result

    return _FALLBACK.handle(text, lower, gui, user_id)
