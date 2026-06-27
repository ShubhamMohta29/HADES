# SQL_INJECTION Security Report

## Status: PASS

## Findings

HADES uses the Supabase Python client for all database access. All queries are constructed via the client's chaining API, which parameterizes every value internally.

**Representative queries in `db.py`:**
```python
# Notes
get_client().table("notes").insert({"user_id": user_id, "content": content}).execute()
get_client().table("notes").select("*").eq("user_id", user_id).execute()
get_client().table("notes").delete().eq("id", rows[0]["id"]).execute()

# Memory
get_client().table("conversation_memory").insert({...}).execute()

# Face encodings
get_client().table("face_encodings").upsert({"user_id": user_id, "encodings": encodings}).execute()

# RPC
get_client().rpc("match_memory", {"query_embedding": vector, "match_user_id": user_id}).execute()
```

No raw SQL strings, no f-strings with SQL keywords, no `.format()` in queries, no string concatenation in SQL. All user-supplied values (`user_id`, `content`, `category`, `role`) are passed as dict values to the Supabase client's parameterized methods. ✅

**`match_memory()` SQL function** (`scripts/supabase_schema.sql`):
```sql
where user_id = match_user_id
  and 1 - (embedding <=> query_embedding) > match_threshold
```
Uses parameterized placeholders (`match_user_id`, `match_threshold`) — no string interpolation. ✅

**No raw SQL in application code** — `supabase_schema.sql` is only run once in the Supabase dashboard by the developer, not executed by the application at runtime.

## What's already secure

- 100% of DB queries use the Supabase client's ORM-style API
- No raw SQL construction in any Python file
- RPC function uses SQL parameters, not string interpolation

## Recommendations

None required. Maintain the policy: all DB access through `db.py` using the Supabase client.
