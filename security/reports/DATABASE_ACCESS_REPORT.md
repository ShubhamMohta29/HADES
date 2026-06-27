# DATABASE_ACCESS Security Report

## Status: PASS

## Findings

All three Supabase tables have Row-Level Security enabled with explicit policies scoped to `auth.uid()`.

**`notes` table** (`scripts/supabase_schema.sql` lines 9–18):
```sql
alter table notes enable row level security;
create policy "Users manage their own notes"
  on notes for all using (auth.uid() = user_id);
```
✅ RLS on, policy scoped to authenticated user.

**`conversation_memory` table** (`scripts/supabase_schema.sql` lines 22–33):
```sql
alter table conversation_memory enable row level security;
create policy "Users manage their own memory"
  on conversation_memory for all using (auth.uid() = user_id);
```
✅ RLS on, policy scoped to authenticated user.

**`face_encodings` table** (`scripts/supabase_schema.sql` lines 64–73):
```sql
alter table face_encodings enable row level security;
create policy "Users manage their own face encodings"
  on face_encodings for all using (auth.uid() = user_id);
```
✅ RLS on, policy scoped to authenticated user.

**`match_memory()` RPC function:**
The function uses `SECURITY INVOKER` (Postgres default for SQL functions), so RLS policies on `conversation_memory` are enforced during function execution. Even if a caller passes a foreign `match_user_id`, the RLS `auth.uid() = user_id` policy prevents reading another user's rows. ✅

**No `USING (true)` policies** — no unrestricted access grants found. ✅

**Anon key access** — The Supabase anon key is used client-side; RLS ensures it can only read/write rows owned by the authenticated user. ✅

## What's at risk

If RLS were disabled or policies were overly permissive, any authenticated user could read all other users' notes, conversation history, and face encodings.

## What's already secure

- All three tables have RLS enabled
- All policies use `auth.uid() = user_id` — no wildcards
- `match_memory()` function does not bypass RLS
- No direct SQL writes in application code; all access goes through `db.py` using the Supabase Python client

## Recommendations

None required. Consider adding RLS to any future tables (e.g., `action_log` in Phase 19) before deployment.
