# ERROR_HANDLING Security Report

## Status: MEDIUM

## Findings

Most of the codebase handles errors well — exceptions are logged and generic messages are returned to the user. One location exposes raw exception strings to the UI.

### VULNERABLE — `gui.py` login/register/magic_link error handlers

```python
# gui.py line 86
self._window.evaluate_js(f"window.showLoginError({json.dumps(str(e))})")

# gui.py line 110
self._window.evaluate_js(f"window.showSignupError({json.dumps(str(e))})")

# gui.py line 122
self._window.evaluate_js(f"window.showLoginError({json.dumps(str(e))})")
```

`str(e)` on a Supabase exception exposes the full error message, which can include:
- HTTP status codes and error bodies: `"Server error '521 ' for url 'https://cazvxwwj...supabase.co/auth/v1/token?grant_type=password'"`
- Internal service identifiers (Supabase project URL)
- Authentication failure details that help enumerate valid email addresses

This was seen in the actual run log: `19:26:27 hades.gui WARNING: Login failed: Server error '521 ' for url 'https://cazvxwwjubhqysewbtbx.supabase.co/auth/v1/token?grant_type=password'` — if this message were shown to the user it would expose the Supabase project ID.

### SAFE — All other error paths

**`brain.py`:**
```python
except GroqError as e:
    log.error("Groq API error: %s", e)
    return "My connection to the language server is disrupted, Sir. Try again in a moment."
```
Returns a generic spoken message; logs full error server-side. ✅

**`main.py` voice loop:**
```python
except Exception as e:
    log.exception("Error in main loop: %s", e)
    _sleeping = False
```
Exception only logged; not surfaced to user. ✅

**`main.py` text handler:**
```python
except Exception as e:
    log.exception("Text command error: %s", e)
```
Exception only logged. ✅

**`vision.py`:**
```python
return f"Vision system error, Sir: {str(e)[:120]}"
```
This returns a truncated error string to the user via speech. This is borderline — it could expose partial Groq API error details. LOW risk since it's spoken output in a local app but worth genericizing.

## What's at risk

A user (or someone observing the login screen) could learn the Supabase project URL, enumerate valid email addresses via differing error messages, or discover service infrastructure details.

## What's already secure

- Voice loop errors: generic messages only
- LLM errors: generic messages only
- DB/Supabase errors in the main command flow: generic messages only

## Recommendations

1. **(MEDIUM — fix)** Replace `str(e)` with generic messages in `gui.py` login/register/magic_link handlers. Log the full exception; show "Authentication failed. Please try again." or similar.
2. **(LOW — fix)** Replace `str(e)[:120]` in `vision.py` with a generic "Vision system error, Sir." Return value.
