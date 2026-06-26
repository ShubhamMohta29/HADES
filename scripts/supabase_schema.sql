-- HADES Supabase Schema
-- Run this once in the Supabase SQL editor:
--   Project → SQL Editor → New query → paste this → Run

-- 1. pgvector extension (skip if already enabled via Database → Extensions)
create extension if not exists vector;

-- 2. Notes table
create table if not exists notes (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid references auth.users on delete cascade not null,
  content    text not null,
  category   text,
  created_at timestamptz default now()
);
alter table notes enable row level security;
create policy "Users manage their own notes"
  on notes for all using (auth.uid() = user_id);

-- 3. Conversation memory table
--    embedding dimension = 384 (all-MiniLM-L6-v2 output size)
create table if not exists conversation_memory (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid references auth.users on delete cascade not null,
  role       text not null check (role in ('user', 'assistant')),
  content    text not null,
  embedding  vector(384),
  created_at timestamptz default now()
);
alter table conversation_memory enable row level security;
create policy "Users manage their own memory"
  on conversation_memory for all using (auth.uid() = user_id);

-- 4. IVFFlat index for fast cosine similarity search on embeddings.
--    lists = 100 is a reasonable default up to ~1M rows; tune if needed.
--    NOTE: IVFFlat requires at least one row to build. Run after inserting data
--    if this fails with "training data must have at least 1 row".
create index if not exists conversation_memory_embedding_idx
  on conversation_memory
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- 5. Semantic search RPC (called by db.retrieve_relevant)
create or replace function match_memory(
  query_embedding vector(384),
  match_user_id   uuid,
  match_count     int   default 5,
  match_threshold float default 0.5
)
returns table (role text, content text, similarity float)
language sql stable as $$
  select
    role,
    content,
    1 - (embedding <=> query_embedding) as similarity
  from conversation_memory
  where user_id = match_user_id
    and 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- 6. Face encodings table
--    encodings is a JSON array of 128-element float arrays (one per captured frame)
create table if not exists face_encodings (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users on delete cascade not null unique,
  encodings   jsonb not null,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);
alter table face_encodings enable row level security;
create policy "Users manage their own face encodings"
  on face_encodings for all using (auth.uid() = user_id);
