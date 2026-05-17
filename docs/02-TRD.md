# Document 02 — TRD: Technical Requirements Document

## Frontend
- **pywebview** wrapping a single-page `frontend/index.html`
- Vanilla HTML/CSS/JS — no framework, no build step
- JS calls Python bridge via `window.pywebview.api.*`
- Python calls JS via `gui.evaluate_js()` for real-time status updates and chat messages

## Backend
- **Python 3.10+** — single-process application. May look into alternatives that are better.
- `main.py` runs the voice loop on a daemon thread; GUI runs on the main thread
- Module architecture: `brain`, `voice`, `commands`, `vision`, `weather`, `news`, `stocks`, `spotify`, `face_auth`, `config`, `gui`
- Intent routing in `main.py:route()` — regex + keyword matching, falls back to Groq LLM

## AI / LLM
- **Groq API** — Llama 3.3 70B Versatile for conversational AI (brain.py)
- **Groq API** — Llama 4 Scout 17B (multimodal) for screen vision (vision.py)
- Conversation history stored as JSON list in `conversation_history.json`; trimmed to system prompt + last 40 messages

## Text-to-Speech
- **Piper TTS** (offline, neural) — `en_GB-alan-medium.onnx` voice model
- Python API path: `piper.PiperVoice` + `sounddevice` for playback
- CLI fallback: `piper` binary on PATH + `soundfile` + `sounddevice`
- Ultimate fallback (no piper): print-only, no audio

## Speech Recognition
- **SpeechRecognition** library — `sr.Recognizer` with Google STT backend
- Wake word detection: polls mic in a loop, checks for "hades" / near-homophones
- Main listen loop: single `listen()` call per turn, 10s timeout

## Third-Party APIs

| Service | Purpose | Tier |
|---|---|---|
| Groq | LLM + vision inference | Free (rate-limited) |
| OpenWeatherMap | Current weather by city | Free |
| NewsAPI | Top headlines / topic search | Free (100 req/day) |
| Yahoo Finance (yfinance) | Stock price lookup | Free |
| CoinGecko | Cryptocurrency price lookup | Free |
| Spotify Web API (spotipy) | Playback control | Free (OAuth) |
| Google STT (via SpeechRecognition) | Voice transcription | Free (internet required) |

## Key Libraries

| Library | Role |
|---|---|
| `groq` | Groq Python SDK |
| `speechrecognition` | STT wrapper |
| `pyaudio` | Microphone input stream |
| `piper-tts` | Offline neural TTS |
| `sounddevice` / `soundfile` | Audio playback |
| `pywebview` | Desktop webview window |
| `spotipy` | Spotify API client |
| `psutil` | CPU / RAM / disk / battery |
| `pyautogui` | Volume keystrokes, screenshots |
| `pycaw` | Windows audio endpoint volume |
| `comtypes` | COM interface for pycaw |
| `opencv-python` | Face detection frames |
| `face_recognition` | Face embedding comparison |
| `Pillow` | Screenshot capture + resize |
| `python-dotenv` | .env loading |
| `numpy` | Audio buffer handling |

## Folder Structure

```
Jarvis/
├── main.py               # entry point, voice loop, intent router
├── brain.py              # Groq LLM, conversation history
├── voice.py              # Piper TTS, SpeechRecognition
├── vision.py             # screen capture + Groq multimodal
├── commands.py           # PC control commands
├── weather.py            # OpenWeatherMap
├── news.py               # NewsAPI
├── stocks.py             # yfinance + CoinGecko
├── spotify.py            # Spotipy playback control
├── face_auth.py          # optional face verification
├── gui.py                # pywebview window + JS bridge
├── config.py             # .env loader, constants
├── frontend/
│   └── index.html        # single-page UI (HTML/CSS/JS)
├── voices/
│   └── en_GB-alan-medium.onnx   # Piper voice model
├── conversation_history.json    # persistent memory (auto-generated)
├── notes.txt                    # notes storage (auto-generated)
├── requirements.txt
├── .env                         # secrets (not committed)
└── docs/                        # planning documents
```

## Environment Variables

```
GROQ_API_KEY            # Groq API key (required)
WEATHER_API_KEY         # OpenWeatherMap API key
NEWS_API_KEY            # NewsAPI.org key
SPOTIFY_CLIENT_ID       # Spotify app client ID
SPOTIFY_CLIENT_SECRET   # Spotify app client secret
SPOTIFY_REDIRECT_URI    # OAuth callback (default: http://127.0.0.1:8888/callback)
DEFAULT_CITY            # default city for weather (default: Toronto)
FACE_AUTH_ENABLED       # "true" to enable face auth gate (default: false)
PIPER_MODEL             # absolute path to .onnx file (default: ./voices/en_GB-alan-medium.onnx)
```

## Constraints

- **Windows only** (pycaw, winsound, rundll32 system calls; face_auth uses Windows camera)
- **Python 3.10+** required (Groq SDK, type hints)
- **Internet required** for: Groq API, Google STT, weather, news, stocks, Spotify
- **Microphone required** for voice mode (text input fallback available in GUI)
- Must stay on free tiers for all APIs
- No database — flat files only (JSON history, TXT notes) [need to change it for better feel]
- Single user, single machine
