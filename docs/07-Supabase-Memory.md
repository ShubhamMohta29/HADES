# 07 — Supabase & Semantic Memory
## Multi-User Data Isolation + Two-Tier Persistent Memory
## Status: **COMPLETE** — all phases shipped (Session 008, 2026-06-02)

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

-- Vector similarity index (cosine distance, IVFFlat for speed at scale).
-- Requires at least one row to build; safe to re-run (IF NOT EXISTS).
CREATE INDEX IF NOT EXISTS conversation_memory_embedding_idx
  ON conversation_memory
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

> Both the `role` CHECK constraint and the IVFFlat index are included in `supabase_schema.sql` (added Session 009 — they were documented here but missing from the SQL file).

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

### 6.1 `db.py` (shipped)

Centralises all Supabase interaction. No other file imports `supabase` directly. See `db.py` for the full implementation. Key additions beyond the original plan:

- `is_available()` — guards all Supabase paths; returns `False` when env vars absent
- Auth helpers: `sign_in`, `sign_up`, `sign_in_magic_link`, `restore_session`, `sign_out`
- Notes: `get_note_categories`, `delete_last_note_db`, `delete_notes_db` (additions)
- Memory: `load_recent`, `clear_memory_db` (additions)
- Lazy init for both client and embedder (avoids import-time cost)
- `sign_in` / `sign_up` use `model_dump(mode='json')` — ensures the session dict written to `~/.jarvis/session.json` contains only JSON-native types (datetimes serialized as ISO strings, not Python `datetime` objects)

### 6.2 `brain.py` changes (shipped)

`think()` accepts an optional `user_id`. When `user_id` is present and Supabase is available, the two-tier path is used: `db.load_recent(user_id, n=12)` + `db.retrieve_relevant(user_id, query, k=5)` → injected as a "Relevant past context" block in the system prompt. Falls back to local JSON otherwise. See `brain.py` for the full implementation.

### 6.3 `commands/notes.py` changes (shipped)

All notes functions now accept `user_id` and call `_use_db(user_id)` to decide path. Additions beyond the original plan: `delete_last_note(user_id)` and `delete_notes(category, user_id)` — both db-aware. See `commands/notes.py` for the full implementation.

---

## 7. Migration Path

| Old | New | Action |
|---|---|---|
| `conversation_history.json` | `conversation_memory` table | Delete local file after first successful Supabase write |
| `notes.txt` | `notes` table | One-time import script to seed existing notes on first login |
| No auth | Supabase Auth session | Add login screen to `gui.py` before main assistant loop |

> **Note**: `notes.txt` lines now carry an optional category tag: `[YYYY-MM-DD HH:MM] [category] content`. The migration script below reads and preserves this tag into the `category` column.

### One-time notes import script (shipped)

`run_once_migrate_notes.py` — prompts for user UUID, reads `notes.txt`, inserts each note into Supabase with timestamp + category preserved, renames `notes.txt` → `notes.txt.bak`. Safe to re-run; checks for file existence first. See the file for full implementation.

---

## 8. Implementation Phases

| Phase | Task | Status | Files touched |
|---|---|---|---|
| 8.1 | Create Supabase project, run `supabase_schema.sql` | ✅ | Supabase dashboard + `supabase_schema.sql` (new) |
| 8.2 | Add `SUPABASE_URL`, `SUPABASE_ANON_KEY` to `.env` + `.env.example` | ✅ | `.env`, `.env.example` |
| 8.3 | Install `supabase` and `sentence-transformers` Python packages | ✅ | `requirements.txt` |
| 8.4 | Write `db.py` | ✅ | new file |
| 8.5 | Add login UI to `gui.py`; store session in `~/.jarvis/session.json` | ✅ | `gui.py` |
| 8.6 | Refactor `brain.py` to use two-tier memory | ✅ | `brain.py` |
| 8.7 | Refactor `commands/notes.py` notes functions to use `db.py` | ✅ | `commands/notes.py` |
| 8.8 | Thread `user_id` through `main.py` intent router | ✅ | `main.py` |
| 8.9 | Write migration script for existing `notes.txt` | ✅ | `run_once_migrate_notes.py` (new) |
| 8.10 | `conversation_history.json` and `notes.txt` kept as local fallback | ✅ (kept) | gitignored; both paths coexist |

> Note: 8.10 was originally "delete local files" but the correct design keeps them as the fallback path for users who do not configure Supabase. The `_use_db(user_id)` helper in `commands.py` and the `use_supabase` flag in `brain.py:think()` select the active path at runtime.

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