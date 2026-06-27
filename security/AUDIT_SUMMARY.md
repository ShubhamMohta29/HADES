# Security Audit Summary

Date: 2026-06-26

## Results

| # | Category | Status | Report | Plan |
|---|---|---|---|---|
| 1 | SECRETS_EXPOSURE | LOW | [report](reports/SECRETS_EXPOSURE_REPORT.md) | — |
| 2 | DATABASE_ACCESS | PASS | [report](reports/DATABASE_ACCESS_REPORT.md) | — |
| 3 | AUTH_MIDDLEWARE | N/A | [report](reports/AUTH_MIDDLEWARE_REPORT.md) | — |
| 4 | ACCESS_CONTROL | N/A | [report](reports/ACCESS_CONTROL_REPORT.md) | — |
| 5 | FRONTEND_SECRETS | PASS | [report](reports/FRONTEND_SECRETS_REPORT.md) | — |
| 6 | SSRF | N/A | [report](reports/SSRF_REPORT.md) | — |
| 7 | CSRF | N/A | [report](reports/CSRF_REPORT.md) | — |
| 8 | SECURITY_HEADERS | N/A | [report](reports/SECURITY_HEADERS_REPORT.md) | — |
| 9 | CORS | N/A | [report](reports/CORS_REPORT.md) | — |
| 10 | RATE_LIMITING | N/A | [report](reports/RATE_LIMITING_REPORT.md) | — |
| 11 | SQL_INJECTION | PASS | [report](reports/SQL_INJECTION_REPORT.md) | — |
| 12 | XSS | LOW | [report](reports/XSS_REPORT.md) | — |
| 13 | PAYMENT_WEBHOOKS | N/A | [report](reports/PAYMENT_WEBHOOKS_REPORT.md) | — |
| 14 | FILE_UPLOADS | MEDIUM → **FIXED** | [report](reports/FILE_UPLOADS_REPORT.md) | [plan](plans/FILE_UPLOADS_PLAN.md) |
| 15 | ERROR_HANDLING | MEDIUM → **FIXED** | [report](reports/ERROR_HANDLING_REPORT.md) | [plan](plans/ERROR_HANDLING_PLAN.md) |
| 16 | PASSWORD_HASHING | N/A | [report](reports/PASSWORD_HASHING_REPORT.md) | — |
| 17 | DEPENDENCIES | MEDIUM → **FIXED** | [report](reports/DEPENDENCIES_REPORT.md) | [plan](plans/DEPENDENCIES_PLAN.md) |

## Critical issues

None. No CRITICAL or HIGH severity findings.

## What was fixed

### FILE_UPLOADS (MEDIUM — fixed)
`face_auth.py` used `pickle.dump` / `pickle.load` for local face encoding storage. A tampered `face_encodings.pkl` can execute arbitrary code on load. Migrated to JSON (`face_encodings.json`) — eliminates the deserialization attack surface entirely. `.gitignore` updated to cover the new filename.

### ERROR_HANDLING (MEDIUM — fixed)
`gui.py` login, register, and magic-link error handlers were passing `str(e)` directly to the frontend, potentially exposing Supabase project URLs, HTTP status details, and service internals. Replaced with static generic messages; full exception still logged at WARNING level. `vision.py` similarly replaced `str(e)[:120]` in the return value with a static message.

### DEPENDENCIES (MEDIUM — fixed)
All packages in `requirements.txt` were unpinned (bare names only). Pinned all packages to exact versions matching the current installed environment. `openwakeword` remains unpinned as it is an optional feature not currently installed in the venv.

## N/A categories — why

HADES is a local Windows desktop application (pywebview). It has no HTTP server, no web API routes, no session cookies, no file upload endpoints, and no payment processing. The following categories do not apply to this architecture:

- **AUTH_MIDDLEWARE** — no HTTP routes; Supabase JWT handles auth
- **ACCESS_CONTROL** — no resource IDs in URLs; Supabase RLS enforces isolation
- **SSRF** — no user-supplied URLs; all fetched URLs are hardcoded
- **CSRF** — no cookies or cross-origin HTTP
- **SECURITY_HEADERS** — no HTTP server
- **CORS** — no HTTP API
- **RATE_LIMITING** — no HTTP endpoints; Supabase handles its own rate limiting
- **PAYMENT_WEBHOOKS** — no payments
- **PASSWORD_HASHING** — delegated entirely to Supabase Auth (bcrypt)

These categories become applicable if a web-facing API or mobile companion is added in v2.0.

## Remaining manual verification

1. **ERROR_HANDLING** — Disconnect from the internet, launch HADES, attempt login — confirm UI shows a generic message with no Supabase URL or HTTP status codes visible.
2. **FILE_UPLOADS** — Delete `face_encodings.pkl` and `face_encodings.json`, run with `FACE_AUTH_ENABLED=true` — confirm `face_encodings.json` is created (not `.pkl`), then restart and confirm face verification succeeds.
3. **DEPENDENCIES** — On a fresh venv, run `pip install -r requirements.txt` and confirm all packages install at the pinned versions with no resolver conflicts.
