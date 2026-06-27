# FRONTEND_SECRETS Security Report

## Status: PASS

## Findings

`frontend/index.html` is the only frontend file. It contains no API keys, tokens, or credentials of any kind.

All sensitive operations (Groq API calls, Supabase auth, weather/news/stock fetches) are performed in Python on the server side. The frontend communicates with Python exclusively via the pywebview bridge (`window.pywebview.api.*`).

**No public-prefix env vars** — HADES does not use Next.js, Vite, or Create React App, so there are no `NEXT_PUBLIC_*`, `VITE_*`, or `REACT_APP_*` variables that could accidentally expose secrets to a bundler.

**API calls from frontend:**
- `window.pywebview.api.send_message(text)` — routes to Python
- `window.pywebview.api.login(email, pass)` — routes to Python → Supabase
- `window.pywebview.api.register(email, pass)` — routes to Python → Supabase
- `window.pywebview.api.magic_link(email)` — routes to Python → Supabase
- `window.pywebview.api.skip_login()` — routes to Python

No direct browser-to-Supabase, browser-to-Groq, or browser-to-any-API calls. ✅

## What's already secure

- Zero API keys in frontend
- All third-party API calls proxied through Python
- No build tooling that could bundle env vars into client code

## Recommendations

None required.
