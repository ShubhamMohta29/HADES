"""Centralized Supabase client, embedding, and data access layer.

All Supabase interaction is contained here. No other file imports `supabase`
directly. When SUPABASE_URL is not set the module is still importable but every
function raises RuntimeError — callers should guard with `db.is_available()`.
"""

import logging
import threading
from config import SUPABASE_URL, SUPABASE_ANON_KEY

log = logging.getLogger("hades.db")

_client = None
_embedder = None
_embedder_lock = threading.Lock()


def is_available() -> bool:
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)


def get_client():
    global _client
    if _client is None:
        if not is_available():
            raise RuntimeError("Supabase is not configured (SUPABASE_URL/SUPABASE_ANON_KEY missing).")
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _client


def _get_embedder():
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                from sentence_transformers import SentenceTransformer
                _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def embed(text: str) -> list:
    return _get_embedder().encode(text, normalize_embeddings=True).tolist()


# ── Auth helpers ─────────────────────────────────────────────────────────────

def sign_in(email: str, password: str) -> dict:
    """Sign in with email + password. Returns the session dict."""
    result = get_client().auth.sign_in_with_password({"email": email, "password": password})
    return result.session.model_dump(mode="json")


def sign_up(email: str, password: str) -> dict:
    """Register a new user. Returns session dict on immediate login, or
    {"pending_confirmation": True} when email confirmation is required."""
    result = get_client().auth.sign_up({"email": email, "password": password})
    if result.session:
        return result.session.model_dump(mode="json")
    return {"pending_confirmation": True}


def sign_in_magic_link(email: str):
    """Send a magic-link OTP email."""
    get_client().auth.sign_in_with_otp({"email": email})


def restore_session(access_token: str, refresh_token: str) -> str | None:
    """Restore a persisted session. Returns the user_id or None on failure."""
    try:
        result = get_client().auth.set_session(access_token, refresh_token)
        return result.user.id if result.user else None
    except Exception as e:
        log.debug("Session restore failed: %s", e)
        return None


def sign_out():
    try:
        get_client().auth.sign_out()
    except Exception as e:
        log.debug("Sign-out error: %s", e)


# ── Notes ────────────────────────────────────────────────────────────────────

def add_note(user_id: str, content: str, category: str = None):
    get_client().table("notes").insert({
        "user_id": user_id,
        "content": content,
        "category": category,
    }).execute()


def get_notes(user_id: str, category: str = None) -> list:
    q = get_client().table("notes").select("*").eq("user_id", user_id)
    if category:
        q = q.eq("category", category)
    return q.order("created_at", desc=True).execute().data or []


def get_note_categories(user_id: str) -> list:
    rows = (
        get_client()
        .table("notes")
        .select("category")
        .eq("user_id", user_id)
        .execute()
        .data or []
    )
    cats = sorted({r["category"] for r in rows if r.get("category")})
    return cats if cats else ["personal", "work"]


def delete_last_note_db(user_id: str) -> bool:
    """Delete the most recently created note. Returns True if a row was deleted."""
    rows = (
        get_client()
        .table("notes")
        .select("id")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        return False
    get_client().table("notes").delete().eq("id", rows[0]["id"]).execute()
    return True


def delete_notes_db(user_id: str, category: str = None) -> int:
    """Delete notes for a user (optionally filtered by category). Returns count deleted."""
    existing = get_notes(user_id, category)
    if not existing:
        return 0
    q = get_client().table("notes").delete().eq("user_id", user_id)
    if category:
        q = q.eq("category", category)
    q.execute()
    return len(existing)


# ── Conversation memory ──────────────────────────────────────────────────────

def save_message(user_id: str, role: str, content: str):
    vector = embed(content)
    get_client().table("conversation_memory").insert({
        "user_id": user_id,
        "role": role,
        "content": content,
        "embedding": vector,
    }).execute()


def load_recent(user_id: str, n: int = 12) -> list:
    """Return the last n messages in chronological order."""
    rows = (
        get_client()
        .table("conversation_memory")
        .select("role,content")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(n)
        .execute()
        .data or []
    )
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def retrieve_relevant(user_id: str, query: str, k: int = 5) -> list:
    """Return up to k semantically relevant past messages via pgvector cosine search."""
    vector = embed(query)
    result = get_client().rpc("match_memory", {
        "query_embedding": vector,
        "match_user_id": user_id,
        "match_count": k,
        "match_threshold": 0.5,
    }).execute()
    return result.data or []


def clear_memory_db(user_id: str):
    get_client().table("conversation_memory").delete().eq("user_id", user_id).execute()


# ── Face encodings ────────────────────────────────────────────────────────────

def save_face_encodings(user_id: str, encodings: list) -> None:
    """Upsert face encodings (list of 128-float lists) for a user."""
    get_client().table("face_encodings").upsert({
        "user_id": user_id,
        "encodings": encodings,
        "updated_at": "now()",
    }).execute()


def load_face_encodings(user_id: str) -> list | None:
    """Return the stored encoding arrays for a user, or None if not found."""
    result = (
        get_client()
        .table("face_encodings")
        .select("encodings")
        .eq("user_id", user_id)
        .execute()
    )
    if result.data:
        return result.data[0]["encodings"]
    return None
