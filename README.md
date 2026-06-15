# H.A.D.E.S — Human Assistance and Decision Engineering System
A fully voice-activated AI assistant inspired by Iron Man's JARVIS, built with Python.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203-orange)
![License](https://img.shields.io/badge/License-MIT-green)

> **Vision:** Be the JARVIS you'd actually trust running on your machine — proactive, conversational, multi-modal, and capable of managing your day, your systems, and your information, while staying fast, private-by-option, and safe with your computer.

---

## Features

Legend: ✅ shipped · 🔜 planned (see [Roadmap](#roadmap))

### Core interaction
| Feature | Status | Description |
|---|---|---|
| Wake Word | ✅ | Say **"HADES"** to activate — no button needed |
| Sleep Mode | ✅ | "sleep"/"goodbye" → mic stays on, listens only for wake word; orb dims |
| AI Conversation | ✅ | Groq LLaMA 3.3 70B with persistent memory |
| Cloud Memory | ✅ | Optional Supabase — two-tier: last 12 turns + top 5 semantic via pgvector |
| Multi-User Auth | ✅ | Email+password or magic link; session persisted across restarts |
| Face Auth | ✅ | Optional face-recognition gate before startup |
| GUI | ✅ | Animated holographic dark UI with text-input fallback |
| **Continuous conversation** | 🔜 | Ask follow-ups without re-saying the wake word; configurable hold-open window |
| **Barge-in / interruptible speech** | 🔜 | Talk over HADES to stop or redirect mid-sentence |
| **Streaming responses** | 🔜 | Begin speaking as tokens arrive — lower perceived latency |
| **Neural wake word** | 🔜 | openWakeWord/Porcupine for far fewer false triggers than fuzzy STT matching |
| **Speaker identification** | 🔜 | Recognize *who* is speaking and load their profile/memory automatically |

### Knowledge & answers
| Feature | Status | Description |
|---|---|---|
| Weather | ✅ | Real-time weather for any city |
| News | ✅ | Top headlines or topic-specific news |
| Stocks & Crypto | ✅ | Live prices via Yahoo Finance & CoinGecko |
| Screen Vision | ✅ | "Look at my screen" — Groq Llama 4 Scout |
| **Web research agent** | 🔜 | Search, open, and summarize pages; multi-source answers with citations |
| **Document & PDF Q&A** | 🔜 | "Summarize this PDF" / "what does this contract say about X" via local RAG |
| **Webcam vision** | 🔜 | Object/scene awareness, OCR ("read this label"), document capture |
| **Calculations & conversions** | 🔜 | Math, unit/currency conversion, quick reference |
| **Translation** | 🔜 | Speak/translate between languages on the fly |

### Productivity & life management
| Feature | Status | Description |
|---|---|---|
| Notes & Reminders | ✅ | Voice notes with categories; timed reminders; delete by category/last |
| Spotify | ✅ | Play, pause, skip, search playlists & songs by voice |
| **Calendar integration** | 🔜 | Google Calendar: read agenda, create/move events, meeting prep, conflict alerts |
| **Email assistant** | 🔜 | Gmail: triage, summarize, draft, and send **with confirmation** |
| **Morning / evening briefings** | 🔜 | Proactive digest: weather, agenda, headlines, markets, "what you missed" |
| **Timers, alarms, stopwatch** | 🔜 | Multiple named timers and alarms by voice |
| **File search** | 🔜 | "Find my resume" / "open the budget spreadsheet" across known folders |
| **Routines / macros** | 🔜 | Chain actions: "Good morning" → lights on + brief + start playlist |

### System & device control
| Feature | Status | Description |
|---|---|---|
| PC Control | ✅ | Volume, apps, shutdown, lock, screenshots, clipboard, CPU/RAM/disk |
| **Smart-home control** | 🔜 | Home Assistant bridge: lights, thermostat, scenes, plugs |
| **Notification awareness** | 🔜 | Read/summarize OS notifications; "what did I miss while away" |
| **Media keys / multi-source audio** | 🔜 | Control any media app via system media keys, not just Spotify |
| **Remote / mobile companion** | 🔜 | Trigger HADES and get responses from a phone on the same network |

### Intelligence & personality
| Feature | Status | Description |
|---|---|---|
| **Proactive nudges** | 🔜 | Context-aware, *rationed* suggestions (e.g., "leave in 10 for your 3pm") |
| **Adjustable persona** | 🔜 | Tone/verbosity/wit dial; multiple TTS voices and emotional inflection |
| **Preference learning** | 🔜 | Learns recurring choices; stores a **user-editable** preferences profile |
| **Mood-adaptive replies** | 🔜 | Reads sentiment from phrasing and adapts brevity/warmth |
| **Developer mode** | 🔜 | Explain/run snippets, git status/commit summaries, project Q&A |

### Extensibility & safety
| Feature | Status | Description |
|---|---|---|
| **Local / offline mode** | 🔜 | Optional local LLM (Ollama) + fully-offline fallback for privacy/no-internet |
| **Skill / plugin system** | 🔜 | Drop-in user skills via a simple manifest; community-extendable command set |
| **Action confirmation** | 🔜 | Destructive actions (shutdown, delete, send) require a spoken/clicked confirm |
| **Untrusted-input handling** | 🔜 | Treat screen/web/news text as data, never as commands to auto-execute |
| **Action log** | 🔜 | Reviewable history of what HADES did and when |
| **Secret redaction** | 🔜 | Never read API keys / passwords aloud or into prompts |

---

## Roadmap

**v0.x (now):** voice loop, conversation + memory, weather/news/stocks/Spotify, PC control, screen vision, notes/reminders, auth, GUI.

**v1.0 — "Smoother JARVIS":** continuous conversation, barge-in, streaming responses, neural wake word, action confirmation + action log, untrusted-input handling, local/offline LLM option.

**v1.5 — "Life manager":** calendar + email, morning/evening briefings, routines/macros, timers/alarms, file search, notification awareness.

**v2.0 — "Anticipatory & extensible":** proactive nudges, preference learning + editable profile, web research agent, document/PDF Q&A, skill/plugin system, smart-home bridge, mobile companion.

**v2.5 — "Multi-modal & personal":** webcam vision, speaker ID + per-user profiles, adjustable persona + emotional TTS, translation, developer mode.

---

## Architecture & Extensibility

HADES is modular: `main.py` runs the voice loop; `router.py` dispatches each recognized intent to the right handler using the **Strategy pattern** — 11 `_Handler` subclasses, each owning one intent, registered in a priority list. To add a new intent, write a subclass and append it to `_HANDLERS`; `route()` itself never changes (OCP). PC commands use the same pattern inside `commands/system.py` with 12 `_CommandHandler` subclasses. Planned **skill system** formalizes this further so anyone can add commands without touching core:

```
skills/
  my_skill/
    skill.json     # name, trigger phrases, required config/keys
    handler.py     # def handle(intent, context) -> spoken_response
```

`main.py` discovers skills at startup, registers their trigger phrases with the intent router, and passes a shared `context` (current user, memory, recent screen text, preferences). This keeps the core stable while the command set grows.

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/ShubhamMohta29/HADES.git
cd HADES
```

### 2. Install — Windows (recommended)

Double-click **`install.bat`**. It will:
- Create a `venv/` virtual environment
- Install all Python dependencies
- Download the Piper TTS CLI binary (no C++ Build Tools required)
- Download the default Piper voice model (~60 MB, `en_GB-alan-medium`)
- Copy `.env.example` → `.env`

Then skip to step 3.

#### Manual install (non-Windows / custom setup)
```bash
pip install -r requirements.txt
cp .env.example .env   # or: copy .env.example .env  on Windows CMD
```

> **Piper TTS voice model** — The default `en_GB-alan-medium` model (~60 MB) is **auto-downloaded on first run** if missing. To pre-download or use a different voice, place the `.onnx` + `.onnx.json` files in `./voices/` and set `PIPER_MODEL=voices/<model>.onnx` in `.env`. All voices: [HuggingFace rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices).

### 3. Configure API keys

Edit `.env` with your keys:

| Key | Where to get it | Required |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Yes |
| `WEATHER_API_KEY` | [openweathermap.org/api](https://openweathermap.org/api) | Optional |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) | Optional |
| `SPOTIFY_CLIENT_ID/SECRET` | [developer.spotify.com](https://developer.spotify.com/dashboard) | Optional |
| `SUPABASE_URL` + `SUPABASE_ANON_KEY` | [supabase.com](https://supabase.com) | Optional |
| `GOOGLE_CLIENT_ID/SECRET` | [console.cloud.google.com](https://console.cloud.google.com) — Calendar/Gmail | Optional (v1.5) |
| `HOME_ASSISTANT_URL/TOKEN` | your Home Assistant instance | Optional (v2.0) |
| `OLLAMA_MODEL` | local model name for offline mode | Optional (v1.0) |

> **Default city:** set `DEFAULT_CITY` (e.g. `DEFAULT_CITY=London`)
>
> **Custom wake words:** `WAKE_WORDS=hades,jarvis` — comma-separated; fuzzy variants auto-derived. `WAKE_DEBOUNCE=2.5` tunes echo protection.
>
> **Local/offline mode (v1.0):** set `LLM_BACKEND=ollama` and `OLLAMA_MODEL=llama3.1:8b` to run inference on-device.

### 4. (Optional) Supabase cloud setup

Without Supabase, HADES stores memory in `conversation_history.json` and notes in `notes.txt`. With Supabase you get cloud-synced memory, multi-user support, and semantic (pgvector) search.

1. Create a free project at [supabase.com](https://supabase.com)
2. Enable the `pgvector` extension: **Database → Extensions → vector**
3. Open the SQL editor (**SQL Editor → New query**), paste the contents of **`scripts/supabase_schema.sql`** and run it — this creates the `notes`, `conversation_memory` tables, RLS policies, and the `match_memory` search function
4. Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to your `.env`
5. *(Only if you have existing notes in `notes.txt`)* Run the one-time migration to import them into Supabase:
   ```bash
   python scripts/run_once_migrate_notes.py
   ```
   The script preserves timestamps and category tags, then renames `notes.txt` to `notes.txt.bak`.

### 5. (Optional) Face authentication

To use face-recognition login (`FACE_AUTH_ENABLED=true`):

1. Set `FACE_AUTH_ENABLED=true` in `.env`
2. Install the extra dependencies (requires [C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)):
   ```bash
   pip install face_recognition
   ```
3. Register your face (run once, look straight at the camera):
   ```bash
   python face_auth.py --register
   ```
   This saves your face encodings to `face_encodings.pkl`. Run it again to re-register.

### 6. (Optional) Pre-flight check

Verify all configured API keys are valid before starting:
```bash
python scripts/smoke_test.py
```
Each key prints `PASS`, `FAIL`, or `SKIP` (if not set). All green → ready to launch.

### 7. Run
```bash
# If you used install.bat:
venv\Scripts\activate
python main.py

# Otherwise:
python main.py
```

---

## Voice Commands

| Say... | Action | Status |
|---|---|---|
| *"Hades"* | Wake up | ✅ |
| *"What's the weather in London"* | Weather | ✅ |
| *"Give me today's news"* / *"News about AI"* | Headlines / topic news | ✅ |
| *"What's Tesla's stock price"* / *"What's Bitcoin at"* | Stock / crypto price | ✅ |
| *"Play [song/playlist]"*, *"Pause/skip/previous"*, *"What's playing"*, *"Shuffle"* | Spotify | ✅ |
| *"Set volume to 60%"* / *"Mute"* | Volume | ✅ |
| *"Open Chrome"* / *"Open YouTube"* / *"Search for [query]"* | Launch / web | ✅ |
| *"Take a screenshot"* / *"What's on my screen"* | Screenshot / screen analysis | ✅ |
| *"What's my clipboard / battery"*, *"CPU / RAM / disk"* | System info | ✅ |
| *"What time/today is it"* | Time / date | ✅ |
| *"Shutdown in 30 minutes"* / *"Restart"* / *"Lock"* | Power (✱ will confirm) | ✅→🔜 |
| *"Remind me in 10 minutes to eat"* | Timed reminder | ✅ |
| *"Take a note: ..."*, *"Read my [category] notes"*, *"Delete my last/[category] notes"* | Notes | ✅ |
| *"Clear memory"* | Reset conversation history | ✅ |
| *"Help"* / *"Commands"* | Command reference card | ✅ |
| *"Goodbye / Sleep / Goodnight / Stand by"* | Sleep mode | ✅ |
| *"What's on my calendar today"* / *"Schedule X at 3pm"* | Calendar | 🔜 |
| *"Read my unread emails"* / *"Draft a reply to ..."* | Email (sends only after confirm) | 🔜 |
| *"Give me my morning brief"* | Proactive digest | 🔜 |
| *"Turn off the living room lights"* | Smart home | 🔜 |
| *"Run my Good Morning routine"* | Macro | 🔜 |
| *"Research [topic] and summarize"* | Web research agent | 🔜 |
| *"Read this PDF"* / *"Summarize this document"* | Document Q&A | 🔜 |
| *"Translate that to Spanish"* | Translation | 🔜 |

---

## Tech Stack

- **LLM:** Groq (LLaMA 3.3 70B Versatile) — free, fast inference · *planned: Ollama local backend*
- **Screen Vision:** Groq (Llama 4 Scout 17B — multimodal, same API key, no extra cost)
- **Speech-to-Text:** SpeechRecognition + Google STT (free, no key needed) · *planned: neural wake word (openWakeWord), barge-in*
- **TTS:** PiperTTS — offline, neural, British male voice; auto-downloads on first run · *planned: multi-voice + emotional inflection*
- **Cloud Memory:** Supabase + pgvector (optional; falls back to local JSON)
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`, 384-dim) — semantic memory search
- **GUI:** PyWebview (animated holographic orb + chat log + text-input fallback)
- **PC Control:** pyautogui, psutil, pycaw, pyperclip
- **APIs:** OpenWeatherMap, NewsAPI, Yahoo Finance, CoinGecko · *planned: Google Calendar/Gmail, Home Assistant*
- **Spotify:** Spotipy

---

## Project Structure

```
HADES/
├── main.py                    # Entry point + voice loop
├── router.py                  # Intent dispatcher (Strategy pattern, 11 handlers)
├── brain.py                   # Groq LLM + two-tier memory (Supabase / local JSON)
├── db.py                      # Supabase client, embeddings, auth, notes, memory
├── gui.py                     # Animated holographic GUI + auth flow
├── config.py                  # .env loader
├── vision.py                  # Groq Llama 4 Scout screen analysis
├── face_auth.py               # Optional face recognition (register + verify)
│
├── voice/                     # Voice I/O package
│   ├── tts.py                 #   Piper TTS + auto-download
│   ├── stt.py                 #   SpeechRecognition STT
│   └── wake.py                #   Wake word detection + debounce
│
├── commands/                  # PC control package (Strategy pattern)
│   ├── system.py              #   12 command handlers: volume, power, apps, reminders…
│   ├── notes.py               #   Notes CRUD (local + Supabase)
│   └── help.py                #   HELP_HTML constant
│
├── services/                  # External data services
│   ├── weather.py             #   OpenWeatherMap
│   ├── news.py                #   NewsAPI
│   ├── stocks.py              #   Yahoo Finance + CoinGecko
│   └── spotify.py             #   Spotify playback control
│
├── scripts/                   # Utility / one-time scripts
│   ├── supabase_schema.sql    #   SQL: tables, RLS, match_memory() RPC
│   ├── run_once_migrate_notes.py  # One-time migration: notes.txt → Supabase
│   └── smoke_test.py          #   Pre-flight API key validation
│
├── frontend/index.html        # Single-page sci-fi UI
├── tests/test_route.py        # 24 unit tests for router.route()
├── install.bat                # Windows one-command installer
├── setup.py                   # pip install -e . packaging
├── requirements.txt
├── .env.example
└── docs/                      # Planning and architecture docs
```

---

## Memory Modes

| Mode | When active | How it works |
|---|---|---|
| **Local** | No Supabase configured | Last 20 turns in `conversation_history.json` |
| **Cloud** | Supabase configured + logged in | Last 12 messages (recency) + top 5 semantic via pgvector cosine search |

---

## Design Principles (for new features)
- **Fast feels smart.** Stream and speak early; never make the user wait in silence.
- **Confirm before consequences.** Anything that deletes, sends, or powers off asks first.
- **Untrusted text is data, not orders.** Content read from the screen, the web, or emails is never executed as a command.
- **Private by option.** Every cloud dependency should have a local/offline path.
- **Personality with restraint.** Witty when welcome, quiet when you're focused.

---

## License
MIT