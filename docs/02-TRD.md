# Document 02 — TRD: Technical Requirements Document

## Frontend
- **pywebview** wrapping a single-page `frontend/index.html`
- Vanilla HTML/CSS/JS — no framework, no build step
- JS calls Python bridge via `window.pywebview.api.*`
- Python calls JS via `gui.evaluate_js()` for real-time status updates, chat messages, and auth events

## Backend
- **Python 3.10+** — single-process application
- `main.py` runs the voice loop on a daemon thread; GUI runs on the main thread
- Module architecture: `brain`, `db`, `voice/` (tts, stt, wake), `commands/` (system, notes, help), `services/` (weather, news, stocks, spotify), `vision`, `face_auth`, `config`, `gui`
- Intent routing in `router.py:route()` — Strategy pattern dispatcher: 13 `_Handler` subclasses, each owning one intent; `route()` iterates `_HANDLERS` and delegates to the first match; falls back to Groq LLM; adding a new intent never modifies `route()` (OCP); `main.py` is the entry point and voice loop only. Includes `_PowerConfirmHandler` (Phase 16) and extended `_DeleteNoteHandler` with confirm gate; `_handle_confirm_state()` manages the `"confirm_action"` pending state alongside the existing `"save_note"` flow

## AI / LLM
- **Groq API** — Llama 3.3 70B Versatile for conversational AI (`brain.py`)
- **Groq API** — Llama 4 Scout 17B (`meta-llama/llama-4-scout-17b-16e-instruct`, multimodal) for screen vision (`vision.py`). Same API key, no extra cost.
- **Memory** — two modes depending on configuration:
  - *Supabase mode* (when `SUPABASE_URL` set + user logged in): two-tier — last 12 messages (recency) + top 5 semantically relevant past turns via pgvector cosine search
  - *Local fallback*: JSON list in `conversation_history.json`; trimmed to system prompt + last 40 messages (20 turns)
- **Streaming (Phase 17 — planned)**: `brain.py:think_stream()` will call Groq with `stream=True` and yield sentence-boundary chunks; `voice/tts.py:speak_streaming()` will pipe each chunk to Piper and play sequentially; `STREAM_CHUNK_MIN_WORDS` (default: 6) prevents single-word fragments causing choppy audio

## Text-to-Speech
- **Piper TTS** (offline, neural) — `en_GB-alan-medium.onnx` voice model
- Python API path: `piper.PiperVoice` + `sounddevice` for playback (preferred — lower latency)
- CLI fallback: `piper` binary on PATH + `soundfile` + `sounddevice`
- Ultimate fallback (no piper): print-only, no audio
- **Auto-download**: if model missing at `./voices/`, `_auto_download_piper()` downloads both `.onnx` + `.onnx.json` from HuggingFace on first `speak()` call

## Speech Recognition
- **SpeechRecognition** library — `sr.Recognizer` with Google STT backend (free, no key required)
- Wake word detection (Phase 14): dual-path in `voice/wake.py` — **neural path** (default): `openwakeword.Model` lazy singleton streams 1280-sample chunks at 16 kHz via `pyaudio`; detects on score > 0.5; **STT fallback**: original fuzzy-match polling loop (active when `NEURAL_WAKE_WORD=false` or `openwakeword` not installed). Both paths respect `WAKE_DEBOUNCE`.
- Main listen loop: single `listen()` call per turn, 10s timeout; returns `MIC_ERROR` sentinel on `OSError` (distinct from `None` for silence)

## Embeddings
- **sentence-transformers** — `all-MiniLM-L6-v2`, 384-dimensional output
- Runs locally (CPU); ~5–20 ms per sentence; ~90 MB model download on first use
- Used by `db.embed()` to embed every conversation message for pgvector storage and semantic search
- `_get_embedder()` uses a double-checked lock (`_embedder_lock`) so concurrent threads share a single model instance rather than each triggering a parallel download

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
| `openwakeword` | Neural wake word detection (Phase 14) — optional; STT fallback when absent |
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
| `PyInstaller` | Bundles HADES into a standalone Windows `.exe` (Phase 18 — dev dependency) |

## Folder Structure

```
HADES/
├── main.py                    # entry point: hades_loop(), handle_text_command(), startup wiring
├── router.py                  # route(), 13-handler intent router, _pending_state (note + confirm flows)
├── brain.py                   # Groq LLM, two-tier memory (Supabase / local JSON)
├── db.py                      # Supabase client, embeddings, auth, notes, memory
├── vision.py                  # screen capture + Groq Llama 4 Scout multimodal
├── face_auth.py               # optional face verification (auto-register on first run + verify); Supabase sync via db.save/load_face_encodings; user_id threaded in from main.py
├── gui.py                     # pywebview window + JS bridge + auth flow
├── config.py                  # .env loader, all constants
│
├── voice/
│   ├── __init__.py            # re-exports: speak, listen, wait_for_wake_word, MIC_ERROR, WAKE_WORDS
│   ├── tts.py                 # Piper TTS: speak(), _init_piper(), auto-download, playback backends
│   ├── stt.py                 # SpeechRecognition: listen(), shared recognizer, MIC_ERROR sentinel
│   └── wake.py                # wake word: neural (openwakeword) + STT fallback; wait_for_wake_word(), listen_for_wake_word_once()
│
├── commands/
│   ├── __init__.py            # re-exports all public names
│   ├── system.py              # Strategy pattern dispatcher: 12 _CommandHandler subclasses; handle_command() = 6-line dispatcher; cancel-shutdown bug fixed
│   ├── notes.py               # save_note, read_notes, delete_last_note, delete_notes, get_existing_categories
│   └── help.py                # HELP_HTML constant
│
├── services/
│   ├── __init__.py
│   ├── weather.py             # OpenWeatherMap
│   ├── news.py                # NewsAPI
│   ├── stocks.py              # yfinance + CoinGecko
│   └── spotify.py             # Spotipy playback control + error summarization
│
├── action_log.py              # (Phase 19 — planned) rolling action log; log_action(); local JSON + optional Supabase
├── voice/
│   └── vad.py                 # (Phase 20 — planned) VoiceActivityDetector; RMS energy per 20 ms frame; interrupt event
├── scripts/
│   ├── supabase_schema.sql    # SQL: notes + conversation_memory + face_encodings + action_log tables, match_memory RPC
│   ├── run_once_migrate_notes.py  # one-time notes.txt → Supabase migration
│   └── smoke_test.py          # pre-flight API key validation
├── install.bat                # Windows one-command installer
├── setup.py                   # pip install -e . packaging
├── frontend/
│   └── index.html             # single-page UI — orb, chat, login panel, help card
├── voices/
│   └── en_GB-alan-medium.onnx   # Piper voice model (gitignored, ~60 MB, auto-downloaded)
├── tests/
│   └── test_route.py          # 33 unit tests for router.route() (pytest, all deps mocked) — includes Phase 16 confirm gate tests
├── conversation_history.json  # local memory fallback (auto-generated, gitignored)
├── notes.txt                  # local notes fallback (gitignored)
├── face_encodings.pkl         # face auth biometric data — local cache; Supabase face_encodings table is primary (gitignored)
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
NEURAL_WAKE_WORD        # "true" (default) to use openwakeword neural model; "false" forces STT fallback
WAKE_MODEL              # path to custom openwakeword .onnx model (optional; empty = all built-in models)
FOLLOWUP_TIMEOUT        # seconds of silence after a reply before returning to standby (default: 15)
CONFIRM_TIMEOUT         # seconds to wait for spoken confirmation on destructive commands (default: 10)
STREAMING_TTS           # "true" (default) — stream Groq response to TTS as sentence chunks arrive (Phase 17)
STREAM_CHUNK_MIN_WORDS  # minimum words before dispatching a chunk to TTS (default: 6) (Phase 17)
ACTION_LOG_ENABLED      # "true" (default) — log all HADES actions to action_log.json (Phase 19)
BARGE_IN_ENABLED        # "true" (default) — VAD thread interrupts TTS on voice detection (Phase 20)
VAD_THRESHOLD           # RMS energy threshold for voice-activity detection (default: 500) (Phase 20)
```

## Constraints

- **Windows primary** (pycaw, winsound, rundll32 system calls). Piper CLI + sounddevice work on Linux/macOS for the audio path, but PC control commands are Windows-only
- **Python 3.10+** required (Groq SDK, union type hints)
- **Internet required** for: Groq API, Google STT, weather, news, stocks, Spotify, Supabase
- **Microphone optional** — `MIC_ERROR` sentinel from `listen()` enables per-call detection; after 3 consecutive failures the GUI shows a text-only warning; reconnect is auto-detected
- **Supabase optional** — all Supabase-dependent features (cloud memory, multi-user, semantic search) degrade gracefully to flat-file fallback when `SUPABASE_URL` is not set
- Must stay on free tiers for all APIs
- Face auth (`face_recognition`) requires C++ Build Tools (dlib dependency); opt-in only via `FACE_AUTH_ENABLED=true`; auto-registers on first run; encodings synced to Supabase `face_encodings` table when a `user_id` is available
