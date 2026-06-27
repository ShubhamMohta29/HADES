# AUTH_MIDDLEWARE Security Report

## Status: N/A

## Findings

HADES is a local desktop application built with pywebview. It has no HTTP server, no API routes, and no middleware stack. There are no inbound network requests from external clients.

Authentication is handled exclusively by Supabase Auth:
- `db.sign_in()` / `db.sign_up()` call the Supabase Auth endpoint and return a session
- The session is stored locally in `~/.jarvis/session.json`
- On startup, `db.restore_session()` validates the token with Supabase before granting access
- All database operations use the authenticated Supabase client, which includes the JWT in every request header

The `gui.py` → Python bridge (`HadesAPI`) is a local IPC mechanism, not a network-facing API.

## What's already secure

- No unauthenticated code paths that reach Supabase data
- Session token validation delegated to Supabase (JWT verification)
- RLS enforces data isolation at the DB layer regardless of application-level auth state

## Recommendations

N/A. If HADES ever gains an HTTP API (e.g., mobile companion in v2.0), auth middleware must be implemented before any data routes are added.
