"""Core AI logic for HADES — Groq Llama 3.3 70B.

Memory strategy:
  Supabase enabled  → Two-tier: last 12 messages (recency) + top 5 semantically
                      relevant past turns (pgvector cosine search).
  Supabase absent   → Single-tier: last 20 turns from conversation_history.json.
"""

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

MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 1024
MAX_HISTORY_TURNS = 20  # local-file fallback only

HISTORY_FILE = Path(__file__).parent / "conversation_history.json"

SYSTEM_PROMPT = """You are HADES (Human Assistance and Decision Engineering System),
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

_lock = threading.Lock()


# ── Local-file memory (fallback when Supabase is not configured) ─────────────

def _default_history():
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def load_memory():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data and data[0].get("role") == "system":
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
    if len(history) <= 1 + MAX_HISTORY_TURNS * 2:
        return history
    return [history[0]] + history[-MAX_HISTORY_TURNS * 2:]


_local_history = load_memory()


# ── Two-tier prompt builder (Supabase path) ───────────────────────────────────

def _build_prompt_supabase(user_id: str, user_message: str, recent: list) -> list:
    import db
    relevant = db.retrieve_relevant(user_id, user_message, k=5)
    memory_block = "\n".join(
        f"[Past {r['role']}]: {r['content']}" for r in relevant
    )
    system = SYSTEM_PROMPT
    if memory_block:
        system += f"\n\n--- Relevant past context ---\n{memory_block}"
    return [{"role": "system", "content": system}] + recent + [
        {"role": "user", "content": user_message}
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def think(user_input: str, user_id: str = None) -> str:
    """Send user input to Groq and return the assistant reply.

    user_id: Supabase user UUID. If provided (and Supabase is configured) the
             two-tier memory path is used. Otherwise falls back to local JSON.
    """
    import db as _db

    use_supabase = bool(user_id and _db.is_available())

    if use_supabase:
        with _lock:
            recent = _db.load_recent(user_id, n=12)
        messages = _build_prompt_supabase(user_id, user_input, recent)
    else:
        with _lock:
            _local_history.append({"role": "user", "content": user_input})
            messages = list(_local_history)

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
        if not use_supabase:
            with _lock:
                if _local_history and _local_history[-1]["role"] == "user":
                    _local_history.pop()
        return "My connection to the language server is disrupted, Sir. Try again in a moment."
    except Exception as e:
        log.exception("Unexpected error in think(): %s", e)
        if not use_supabase:
            with _lock:
                if _local_history and _local_history[-1]["role"] == "user":
                    _local_history.pop()
        return "I've encountered an unexpected fault, Sir. My apologies."

    if use_supabase:
        try:
            _db.save_message(user_id, "user", user_input)
            _db.save_message(user_id, "assistant", reply)
        except Exception as e:
            log.warning("Failed to persist to Supabase: %s", e)
    else:
        with _lock:
            _local_history.append({"role": "assistant", "content": reply})
            trimmed = _trim(_local_history)
            _local_history[:] = trimmed
            save_memory(_local_history)

    return reply


def clear_memory(user_id: str = None) -> str:
    import db as _db
    if user_id and _db.is_available():
        try:
            _db.clear_memory_db(user_id)
        except Exception as e:
            log.warning("Failed to clear Supabase memory: %s", e)
    global _local_history
    with _lock:
        _local_history = _default_history()
        save_memory(_local_history)
    return "Memory cleared, Sir."
