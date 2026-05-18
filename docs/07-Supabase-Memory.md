# 07 — Supabase & Semantic Memory Plan
## Multi-User Data Isolation + Two-Tier Persistent Memory

---

## 1. Why Supabase

| Need | Solution |
|---|---|
| Multi-user data isolation | Row-Level Security (RLS) — enforced at DB level, not app level |
| User authentication | Supabase Auth built-in (email/password, magic link, OAuth) |
| Relational data (notes) | PostgreSQL |
| Long-term semantic memory | `pgvector` extension — vector DB inside the same Postgres instance |
| Free tier viability | Pausing is a non-issue once real users are active; all four needs from one service |

Alternatives like Turso or PocketBase require building user isolation manually and don't have a native vector store. Firebase has no SQL and no pgvector. For a multi-user deployed app with semantic memory, Supabase is the correct single-service answer.

---

## 2. The Context Loss Problem

### Current behaviour
`brain.py` trims conversation history to `system prompt + last 40 messages (20 turns)`. Everything older is permanently discarded. Jarvis cannot remember anything said more than ~10 exchanges ago.

### Why raising the trim limit doesn't fix it
LLM context windows are finite and expensive to fill. Sending 200 past messages on every request is slow, costly, and still loses everything beyond that. The problem is structural, not a matter of tuning the number.

### Solution: Two-Tier Memory

```
┌─────────────────────────────────────────────────────────┐
│                   PROMPT CONSTRUCTION                   │
│                                                         │
│  [System Prompt]                                        │
│       +                                                 │
│  [Long-Term: Top 5 semantically relevant past turns]   │  ← retrieved by vector search
│       +                                                 │
│  [Short-Term: Last 12 messages verbatim]               │  ← recency window
│       +                                                 │
│  [Current user message]                                 │
└─────────────────────────────────────────────────────────┘
```

Every message (user + assistant) is embedded and stored in Supabase with a vector. On each new message, a similarity search retrieves the most contextually relevant past exchanges — even if they happened weeks ago — and injects them into the prompt. The model gets both recency and depth without filling the window with irrelevant old messages.

---

## 3. Database Schema

### 3.1 Enable pgvector

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Run once in the Supabase SQL editor after creating your project.

### 3.2 Tables

```sql
-- Notes: replaces notes.txt
CREATE TABLE notes (
  id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID        REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  content     TEXT        NOT NULL,
  category    TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation memory: replaces conversation_history.json
CREATE TABLE conversation_memory (
  id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID        REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
  content     TEXT        NOT NULL,
  embedding   VECTOR(384),             -- matches all-MiniLM-L6-v2 output dimensions
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index (cosine distance, IVFFlat for speed at scale)
CREATE INDEX ON conversation_memory
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

### 3.3 Row-Level Security

```sql
-- Notes: users can only touch their own rows
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "own notes only" ON notes
  USING      (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- Memory: users can only touch their own rows
ALTER TABLE conversation_memory ENABLE ROW LEVEL SECURITY;

CREATE POLICY "own memory only" ON conversation_memory
  USING      (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());
```

RLS is enforced at the Postgres level. Even if application code has a bug, user A cannot read user B's data.

### 3.4 Semantic search function

```sql
CREATE OR REPLACE FUNCTION match_memory(
  query_embedding VECTOR(384),
  match_user_id   UUID,
  match_count     INT DEFAULT 5,
  match_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (
  id         UUID,
  role       TEXT,
  content    TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.id,
    m.role,
    m.content,
    1 - (m.embedding <=> query_embedding) AS similarity
  FROM conversation_memory m
  WHERE m.user_id = match_user_id
    AND 1 - (m.embedding <=> query_embedding) > match_threshold
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

---

## 4. Embedding Model

### Choice: `sentence-transformers/all-MiniLM-L6-v2`

| Property | Value |
|---|---|
| Dimensions | 384 |
| Size on disk | ~90 MB |
| Inference | Local CPU, ~5–20 ms per sentence |
| Cost | Free, no API key, runs offline |
| Quality | Good semantic similarity for conversational text |

This runs locally on the user's machine (same as Piper TTS), which means zero embedding API cost and works offline. For a future server-side deployment, swap to `text-embedding-3-small` (OpenAI) or `embed-english-light-v3.0` (Cohere) — both have generous free tiers and the dimension change only requires updating the `VECTOR(384)` column and the index.

### Install

```
pip install sentence-transformers
```

---

## 5. Auth Integration

### Flow for desktop app (pywebview)

```
App launch
    │
    ▼
Check local session token (.env or ~/.jarvis/session)
    │
    ├─ Valid token ──► Load user profile ──► Start assistant
    │
    └─ No/expired ──► Show login panel in pywebview GUI
                           │
                           ├─ Email + password ──► supabase.auth.sign_in_with_password()
                           │
                           └─ Magic link ──────► supabase.auth.sign_in_with_otp()
```

The Supabase Python client (`supabase-py`) handles token refresh automatically. Store the session in a local file outside the project directory (e.g., `~/.jarvis/session.json`) so it persists across app restarts without being committed to git.

### New .env keys

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

The anon key is safe to ship — RLS ensures it can only access data the authenticated user owns.

---

## 6. Code Changes

### 6.1 New file: `db.py`

Centralises all Supabase interaction. No other file should import `supabase` directly.

```python
from supabase import create_client
from sentence_transformers import SentenceTransformer
from config import SUPABASE_URL, SUPABASE_ANON_KEY

_client = None
_embedder = SentenceTransformer("all-MiniLM-L6-v2")

def get_client():
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _client

def embed(text: str) -> list[float]:
    return _embedder.encode(text, normalize_embeddings=True).tolist()

# --- Notes ---

def add_note(user_id: str, content: str, category: str = None):
    get_client().table("notes").insert({
        "user_id": user_id,
        "content": content,
        "category": category,
    }).execute()

def get_notes(user_id: str, category: str = None) -> list[dict]:
    q = get_client().table("notes").select("*").eq("user_id", user_id)
    if category:
        q = q.eq("category", category)
    return q.order("created_at", desc=True).execute().data

# --- Memory ---

def save_message(user_id: str, role: str, content: str):
    vector = embed(content)
    get_client().table("conversation_memory").insert({
        "user_id": user_id,
        "role": role,
        "content": content,
        "embedding": vector,
    }).execute()

def retrieve_relevant(user_id: str, query: str, k: int = 5) -> list[dict]:
    vector = embed(query)
    result = get_client().rpc("match_memory", {
        "query_embedding": vector,
        "match_user_id": user_id,
        "match_count": k,
        "match_threshold": 0.5,
    }).execute()
    return result.data
```

### 6.2 `brain.py` changes

Replace the JSON file read/write with Supabase calls. The prompt construction becomes:

```python
def build_prompt(user_id: str, user_message: str, recent_history: list) -> list:
    # Long-term: semantically relevant past turns
    relevant = retrieve_relevant(user_id, user_message, k=5)
    memory_block = "\n".join(
        f"[Past {r['role']}]: {r['content']}" for r in relevant
    )

    system = get_system_prompt()
    if memory_block:
        system += f"\n\n--- Relevant past context ---\n{memory_block}"

    return [{"role": "system", "content": system}] + recent_history + [
        {"role": "user", "content": user_message}
    ]

def think(user_id: str, user_message: str) -> str:
    with history_lock:
        recent = load_recent(user_id, n=12)   # last 12 messages from Supabase

    messages = build_prompt(user_id, user_message, recent)
    response = groq_client.chat.completions.create(
        model=MODEL, messages=messages
    ).choices[0].message.content

    save_message(user_id, "user", user_message)
    save_message(user_id, "assistant", response)

    return response
```

`load_recent()` queries `conversation_memory` ordered by `created_at DESC LIMIT 12` for the given `user_id`, then reverses the result for chronological order.

### 6.3 `commands.py` changes

Replace `notes.txt` append/read with `db.add_note()` and `db.get_notes()`.

```python
# Before
def save_note(text):
    with open("notes.txt", "a") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M}] {text}\n")

# After
def save_note(user_id: str, text: str, category: str = None):
    db.add_note(user_id, text, category)
```

The `user_id` flows in from the authenticated session stored in `main.py` at startup.

---

## 7. Migration Path

| Old | New | Action |
|---|---|---|
| `conversation_history.json` | `conversation_memory` table | Delete local file after first successful Supabase write |
| `notes.txt` | `notes` table | One-time import script to seed existing notes on first login |
| No auth | Supabase Auth session | Add login screen to `gui.py` before main assistant loop |

> **Note**: `notes.txt` lines now carry an optional category tag: `[YYYY-MM-DD HH:MM] [category] content`. The migration script below reads and preserves this tag into the `category` column.

### One-time notes import script

```python
# run_once_migrate_notes.py
from db import get_client, embed
import re

user_id = input("Your user_id: ")

with open("notes.txt") as f:
    for line in f:
        # Format: [timestamp] [category?] content
        m = re.match(r"\[(.+?)\]\s*(?:\[([a-zA-Z]+)\]\s*)?(.+)", line.strip())
        if m:
            timestamp, category, content = m.groups()
            get_client().table("notes").insert({
                "user_id": user_id,
                "content": content.strip(),
                "category": category,           # None if no tag
                "created_at": timestamp,
            }).execute()

print("Migration complete.")
```

---

## 8. Implementation Phases

| Phase | Task | Files touched |
|---|---|---|
| 8.1 | Create Supabase project, run SQL from §3 | Supabase dashboard |
| 8.2 | Add `SUPABASE_URL`, `SUPABASE_ANON_KEY` to `.env` + `.env.example` | `.env`, `.env.example` |
| 8.3 | Install `supabase` and `sentence-transformers` Python packages | `requirements.txt` |
| 8.4 | Write `db.py` (§6.1) | new file |
| 8.5 | Add login UI to `gui.py`; store session in `~/.jarvis/session.json` | `gui.py` |
| 8.6 | Refactor `brain.py` to use two-tier memory (§6.2) | `brain.py` |
| 8.7 | Refactor `commands.py` notes functions to use `db.py` (§6.3) | `commands.py` |
| 8.8 | Thread `user_id` through `main.py` intent router | `main.py` |
| 8.9 | Run migration script for existing `notes.txt` | `run_once_migrate_notes.py` |
| 8.10 | Delete `conversation_history.json` and `notes.txt` from repo | repo cleanup |

---

## 9. What This Unlocks

| Capability | Before | After |
|---|---|---|
| Context window | Last ~20 turns | Last 12 turns + top 5 relevant from all time |
| Memory lifespan | Session only | Permanent |
| Multi-user | Single user (flat files) | Unlimited users, fully isolated |
| Notes search | Manual grep of text file | Query by category, date, or semantic similarity |
| Cross-device sync | No | Yes (data lives in Supabase) |
| Data safety | Local file only | Cloud-persisted with backups |