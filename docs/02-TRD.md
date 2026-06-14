# Document 02 — TRD: Technical Requirements Document

## Frontend
- **pywebview** wrapping a single-page `frontend/index.html`
- Vanilla HTML/CSS/JS — no framework, no build step
- JS calls Python bridge via `window.pywebview.api.*`
- Python calls JS via `gui.evaluate_js()` for real-time status updates, chat messages, and auth events

## Backend
- **Python 3.10+** — single-process application
- `main.py` runs the voice loop on a daemon thread; GUI runs on the main thread
- Module architecture: `brain`, `db`, `voice`, `commands`, `vision`, `weather`, `news`, `stocks`, `spotify`, `face_auth`, `config`, `gui`
- Intent routing in `main.py:route()` — regex + keyword matching, 13-step priority chain, falls back to Groq LLM

## AI / LLM
- **Groq API** — Llama 3.3 70B Versatile for conversational AI (`brain.py`)
- **Groq API** — Llama 4 Scout 17B (`meta-llama/llama-4-scout-17b-16e-instruct`, multimodal) for screen vision (`vision.py`). Same API key, no extra cost.
- **Memory** — two modes depending on configuration:
  - *Supabase mode* (when `SUPABASE_URL` set + user logged in): two-tier — last 12 messages (recency) + top 5 semantically relevant past turns via pgvector cosine search
  - *Local fallback*: JSON list in `conversation_history.json`; trimmed to system prompt + last 40 messages (20 turns)

## Text-to-Speech
- **Piper TTS** (offline, neural) — `en_GB-alan-medium.onnx` voice model
- Python API path: `piper.PiperVoice` + `sounddevice` for playback (preferred — lower latency)
- CLI fallback: `piper` binary on PATH + `soundfile` + `sounddevice`
- Ultimate fallback (no piper): print-only, no audio
- **Auto-download**: if model missing at `./voices/`, `_auto_download_piper()` downloads both `.onnx` + `.onnx.json` from HuggingFace on first `speak()` call

## Speech Recognition
- **SpeechRecognition** library — `sr.Recognizer` with Google STT backend (free, no key required)
- Wake word detection: polls mic in a loop; checks transcript against `WAKE_WORDS` frozenset (fuzzy variants per word); `WAKE_DEBOUNCE` suppresses double-fire
- Main listen loop: single `listen()` call per turn, 10s timeout; returns `MIC_ERROR` sentinel on `OSError` (distinct from `None` for silence)

## Embeddings
- **sentence-transformers** — `all-MiniLM-L6-v2`, 384-dimensional output
- Runs locally (CPU); ~5–20 ms per sentence; ~90 MB model download on first use
- Used by `db.embed()` to embed every conversation message for pgvector storage and semantic search

## Third-Party APIs

| Service | Purpose | Tier |
|---|---|---|
| Groq | LLM conversation + screen vision inference | Free (rate-limited) |
| Supabase | Auth, notes DB, conversation memory + vector search | Free tier |
| OpenWeatherMap | Current weather by city | Free |
| NewsAPI | Top headlines / topic search | Free (100 req/day) |
| Yahoo Finance (yfinance) | Stock price lookup | Free |
| CoinGecko | Cryptocurrency price lookup | Free |
| Spotify Web API (spotipy) | Playback control | Free (OAuth) |
| Google STT (via SpeechRecognition) | Voice transcription | Free (internet required) |

## Key Libraries

| Library | Role |
|---|---|
| `groq` | Groq Python SDK (LLM + vision) |
| `supabase` | Supabase Python client (auth, DB, RPC) |
| `sentence-transformers` | Local embedding model (all-MiniLM-L6-v2) |
| `openwakeword` | Neural wake word detection — Phase 14 (planned) |
| `speechrecognition` | STT wrapper |
| `pyaudio` | Microphone input stream |
| `piper-tts` | Offline neural TTS (Python API path) |
| `sounddevice` / `soundfile` | Audio playback |
| `pywebview` | Desktop webview window |
| `spotipy` | Spotify API client |
| `psutil` | CPU / RAM / disk / battery |
| `pyautogui` | Volume keystrokes, screenshots |
| `pyperclip` | Clipboard read |
| `pycaw` | Windows audio endpoint volume |
| `comtypes` | COM interface for pycaw |
| `opencv-python` | Face detection frames |
| `face_recognition` | Face embedding comparison (optional — needs C++ Build Tools) |
| `Pillow` | Screenshot capture + resize |
| `python-dotenv` | .env loading |
| `numpy` | Audio buffer handling + resampling |
| `requests` | HTTP calls (weather, news, crypto) |
| `pytest` | Unit test runner (`tests/`) |

## Folder Structure

```
HADES/
├── main.py                    # entry point, voice loop, 13-step intent router
├── brain.py                   # Groq LLM, two-tier memory (Supabase / local JSON)
├── db.py                      # Supabase client, embeddings, auth, notes, memory
├── voice.py                   # Piper TTS + auto-download, SpeechRecognition, wake word
├── vision.py                  # screen capture + Groq Llama 4 Scout multimodal
├── commands.py                # PC control, notes + deletion, HELP_HTML
├── weather.py                 # OpenWeatherMap
├── news.py                    # NewsAPI
├── stocks.py                  # yfinance + CoinGecko
├── spotify.py                 # Spotipy playback control + error summarization
├── face_auth.py               # optional face verification (register + verify)
├── gui.py                     # pywebview window + JS bridge + auth flow
├── config.py                  # .env loader, all constants
├── supabase_schema.sql        # SQL: notes + conversation_memory tables, match_memory RPC
├── run_once_migrate_notes.py  # one-time notes.txt → Supabase migration
├── smoke_test.py              # pre-flight API key validation
├── install.bat                # Windows one-command installer
├── setup.py                   # pip install -e . packaging
├── frontend/
│   └── index.html             # single-page UI — orb, chat, login panel, help card
├── voices/
│   └── en_GB-alan-medium.onnx   # Piper voice model (gitignored, ~60 MB, auto-downloaded)
├── tests/
│   └── test_route.py          # 24 unit tests for route() (pytest, all deps mocked)
├── conversation_history.json  # local memory fallback (auto-generated, gitignored)
├── notes.txt                  # local notes fallback (gitignored)
├── face_encodings.pkl         # face auth biometric data (gitignored)
├── requirements.txt
├── .env                       # secrets (not committed)
└── docs/                      # planning documents
```

## Environment Variables

```
GROQ_API_KEY            # Groq API key (required)
WEATHER_API_KEY         # OpenWeatherMap API key
NEWS_API_KEY            # NewsAPI.org key
SPOTIFY_CLIENT_ID       # Spotify app client ID
SPOTIFY_CLIENT_SECRET   # Spotify app client secret
SPOTIFY_REDIRECT_URI    # OAuth callback (default: http://127.0.0.1:8888/callback)
SUPABASE_URL            # Supabase project URL (optional; enables cloud memory + auth)
SUPABASE_ANON_KEY       # Supabase anon key (optional; safe to ship — RLS enforces isolation)
DEFAULT_CITY            # default city for weather (default: Toronto)
FACE_AUTH_ENABLED       # "true" to enable face auth gate (default: false)
PIPER_MODEL             # path to .onnx file (default: ./voices/en_GB-alan-medium.onnx)
WAKE_WORDS              # comma-separated wake words (default: hades); fuzzy sets for hades/jarvis/friday
WAKE_DEBOUNCE           # seconds to suppress re-trigger after wake word fires (default: 2.5)
```

## Constraints

- **Windows primary** (pycaw, winsound, rundll32 system calls). Piper CLI + sounddevice work on Linux/macOS for the audio path, but PC control commands are Windows-only
- **Python 3.10+** required (Groq SDK, union type hints)
- **Internet required** for: Groq API, Google STT, weather, news, stocks, Spotify, Supabase
- **Microphone optional** — `MIC_ERROR` sentinel from `listen()` enables per-call detection; after 3 consecutive failures the GUI shows a text-only warning; reconnect is auto-detected
- **Supabase optional** — all Supabase-dependent features (cloud memory, multi-user, semantic search) degrade gracefully to flat-file fallback when `SUPABASE_URL` is not set
- Must stay on free tiers for all APIs
- Face auth (`face_recognition`) requires C++ Build Tools (dlib dependency); opt-in only via `FACE_AUTH_ENABLED=true`
