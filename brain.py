"""Core AI logic for HADES — Groq Llama 3.3 70B with persistent, trimmed memory."""

import json
import threading
import logging
from pathlib import Path
from groq import Groq, GroqError
from config import GROQ_API_KEY

log = logging.getLogger("hades.brain")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

client = Groq(api_key=GROQ_API_KEY)

# Model & memory settings
MODEL = "llama-3.3-70b-versatile"   # upgraded from llama-3.1-8b-instant
MAX_TOKENS = 400
MAX_HISTORY_TURNS = 20              # keep system prompt + last N user/assistant pairs

HISTORY_FILE = Path(__file__).parent / "conversation_history.json"

SYSTEM_PROMPT = """You are HADES (Human Assistance and Decision Engine System),
an AI assistant. You are highly intelligent, witty, and
occasionally sarcastic. Address the user as Sir by default, but vary it —
sometimes use their name if given, sometimes nothing at all.

Rules:
- Be concise unless asked for detail. Voice output means long answers are painful.
- Never refuse without offering an alternative.
- Your responses will be spoken aloud, so avoid markdown, bullet points, or code
  blocks unless specifically asked. Write naturally, as if speaking.
- Keep responses under 3 sentences when possible.

Tone examples:
- "Certainly, Sir. Right away."
- "I've taken the liberty of preparing that for you."
- "Might I suggest an alternative approach?"
- "All systems functioning within normal parameters."
"""

# Thread-safe access to conversation history
_lock = threading.Lock()


def _default_history():
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def load_memory():
    """Load conversation history from disk, or return a fresh one."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data and data[0].get("role") == "system":
                    # Refresh system prompt in case we've updated it
                    data[0]["content"] = SYSTEM_PROMPT
                    return data
        except Exception as e:
            log.warning("Could not load history (%s). Starting fresh.", e)
    return _default_history()


def save_memory(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        log.warning("Could not save history: %s", e)


def _trim(history):
    """Keep system prompt + last MAX_HISTORY_TURNS * 2 messages."""
    if len(history) <= 1 + MAX_HISTORY_TURNS * 2:
        return history
    return [history[0]] + history[-MAX_HISTORY_TURNS * 2 :]


conversation_history = load_memory()


def think(user_input: str) -> str:
    """Send user input + history to Groq, return assistant reply."""
    with _lock:
        conversation_history.append({"role": "user", "content": user_input})
        messages = list(conversation_history)  # snapshot for the API call

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
    except GroqError as e:
        log.error("Groq API error: %s", e)
        # Roll back the user message we just appended
        with _lock:
            if conversation_history and conversation_history[-1]["role"] == "user":
                conversation_history.pop()
        return "My connection to the language server is disrupted, Sir. Try again in a moment."
    except Exception as e:
        log.exception("Unexpected error in think(): %s", e)
        with _lock:
            if conversation_history and conversation_history[-1]["role"] == "user":
                conversation_history.pop()
        return "I've encountered an unexpected fault, Sir. My apologies."

    with _lock:
        conversation_history.append({"role": "assistant", "content": reply})
        trimmed = _trim(conversation_history)
        conversation_history[:] = trimmed
        save_memory(conversation_history)

    return reply


def clear_memory() -> str:
    """Reset conversation to just the system prompt."""
    global conversation_history
    with _lock:
        conversation_history = _default_history()
        save_memory(conversation_history)
    return "Memory cleared, Sir."
