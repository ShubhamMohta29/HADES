# RATE_LIMITING Security Report

## Status: N/A

## Findings

HADES is a local desktop application with no HTTP endpoints. There are no login, registration, or password-reset HTTP routes to rate-limit.

The login UI in `frontend/index.html` calls `window.pywebview.api.login()` which calls `db.sign_in()` → Supabase Auth. Supabase Auth enforces its own rate limits on the auth endpoint (typically 10 failed attempts triggers a cooldown). Application-level rate limiting is not applicable.

## Recommendations

N/A for the current architecture. If a future web API is added, apply rate limiting to all auth endpoints: block after 10 failed attempts per IP per 15 minutes, return HTTP 429, and do not trust `X-Forwarded-For` unless behind a verified reverse proxy.
