# SECRETS_EXPOSURE Security Report

## Status: LOW

## Findings

All secrets are loaded via `config.py` using `os.getenv()` from a `.env` file. No hardcoded credentials exist in any source file.

**`.gitignore` check** — `.env` is listed on line 2. `git ls-files .env` returns nothing. ✅

**Source file scan** — `grep` for `password =`, `secret =`, `api_key =`, `Bearer`, `AKIA` across all `.py`/`.html`/`.js` files returns only references to variables (`GROQ_API_KEY`, `SPOTIFY_CLIENT_SECRET`), never literal values. ✅

**`.env.example`** — Contains placeholder strings only (`"your_groq_api_key_here"`, empty values for Supabase). No real credentials. ✅

**Frontend** — `frontend/index.html` contains no API keys or credentials. All API calls go through the Python bridge (`window.pywebview.api.*`). ✅

**Gitignored sensitive files:**
- `.env` ✅
- `face_encodings.pkl` ✅
- `conversation_history.json` ✅
- `notes.txt` / `notes.txt.bak` ✅
- `.cache` / `.cache-*` (Spotify OAuth) ✅

**Minor finding — `pickle` serialization:**
`face_auth.py` uses `pickle.dump` / `pickle.load` on `face_encodings.pkl`. Per CLAUDE.md security rules: "NEVER use pickle.loads, pickle.load, or any deserialization on user-supplied data." The file is local (not network-supplied), but a tampered `.pkl` file on disk can execute arbitrary code on load. Migrating to JSON eliminates this class of risk. Tracked under FILE_UPLOADS_REPORT.md.

## What's at risk

If `.env` were committed: all API keys (Groq, Supabase, Spotify, weather, news) would be permanently in git history, even if the file were later deleted.

## What's already secure

- `.env` correctly excluded from version control
- `.env.example` uses only placeholders
- No secrets in frontend code
- All credential loading centralised in `config.py`

## Recommendations

1. (LOW) Migrate `face_encodings.pkl` from pickle to JSON — see FILE_UPLOADS_REPORT.md.
2. (INFO) Consider adding `~/.jarvis/session.json` to documentation as a file to exclude from backups (it holds Supabase auth tokens).
