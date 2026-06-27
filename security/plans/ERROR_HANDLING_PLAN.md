# ERROR_HANDLING Fix Plan

## Changes

- `gui.py` — Replace `str(e)` with generic error messages in `login()`, `register()`, and `magic_link()` handlers. Log full exception before replacing.
- `vision.py` — Replace `str(e)[:120]` with a static "Vision system error, Sir." message.

## New files

None.

## Verification goals

- [ ] Login with wrong password shows "Authentication failed. Please check your credentials and try again." — not the Supabase error body
- [ ] Login with no internet shows a generic "Could not reach the authentication server. Please try again." — not the Supabase URL or HTTP details
- [ ] Full exception is still written to the log (WARNING level)
- [ ] `grep -n "str(e)" gui.py` returns no results in error-display paths
- [ ] Vision error path returns a static string with no `str(e)` interpolation

## Manual verification (for the human)

- Disconnect from the internet, launch HADES, attempt login — confirm the UI shows a friendly message with no Supabase URL or HTTP status codes
- Trigger a vision error (e.g., disconnect from Groq) and say "what's on my screen" — confirm the spoken response is generic
