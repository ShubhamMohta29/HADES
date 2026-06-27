# ACCESS_CONTROL Security Report

## Status: N/A

## Findings

No resource IDs are exposed in URL paths, query params, or request bodies accessible to external callers — HADES has no HTTP API.

Access control for Supabase data is enforced entirely by Row-Level Security policies (see DATABASE_ACCESS_REPORT.md). The `user_id` used in every DB call comes from the authenticated Supabase session, not from user-controlled input:

- `main.py` receives `user_id` from `_on_auth_complete(user_id)` — sourced from `db.restore_session()` or `db.sign_in()` response
- `user_id` is passed as a trusted parameter through `hades_loop()` → `route()` → every handler → `db.*` functions
- No handler accepts a `user_id` from a user message or text input — the user cannot specify whose data to access

## What's already secure

- `user_id` is always server-derived (from Supabase JWT), never client-supplied
- Supabase RLS provides a second enforcement layer: even if `user_id` were manipulated in application code, the DB would reject cross-user queries

## Recommendations

N/A for the current architecture. If a future REST API is added, every resource endpoint must independently verify `current_user.id == resource.owner_id` as a separate check from authentication.
