# H.A.D.E.S — Human Assistance and Decision Engineering System
A fully voice-activated AI assistant inspired by Iron Man's JARVIS, built with Python.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

| Feature | Description |
|---|---|
| Wake Word | Say **"HADES"** to activate — no button needed |
| Sleep Mode | Say "sleep", "goodbye", etc. — mic stays on but only listens for wake word; orb dims |
| AI Conversation | Powered by Groq LLaMA 3.3 70B with persistent memory |
| Cloud Memory | Optional Supabase backend — two-tier memory: last 12 turns + top 5 semantically relevant via pgvector |
| Multi-User Auth | Login/signup with email+password or magic link; session persisted across restarts |
| Weather | Real-time weather for any city |
| News | Top headlines or topic-specific news |
| Stocks & Crypto | Live prices via Yahoo Finance & CoinGecko |
| Spotify | Play, pause, skip, search playlists & songs by voice |
| PC Control | Volume, apps, shutdown, lock, screenshots, clipboard, CPU/RAM/disk |
| Screen Vision | Ask HADES to look at your screen — powered by Groq Llama 4 Scout |
| Notes & Reminders | Voice-driven notes with categories, timed reminders, delete by category or last entry |
| Face Auth | Optional face recognition gate before HADES starts |
| GUI | Animated holographic dark-themed interface with text input fallback |

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/ShubhamMohta29/HADES.git
cd HADES
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API keys
```bash
cp .env.example .env
```

Edit `.env` with your keys:

| Key | Where to get it | Required |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Yes |
| `WEATHER_API_KEY` | [openweathermap.org/api](https://openweathermap.org/api) | Optional |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) | Optional |
| `SPOTIFY_CLIENT_ID/SECRET` | [developer.spotify.com](https://developer.spotify.com/dashboard) | Optional |
| `SUPABASE_URL` + `SUPABASE_ANON_KEY` | [supabase.com](https://supabase.com) | Optional |

> **Default city:** set `DEFAULT_CITY` (e.g. `DEFAULT_CITY=London`)
>
> **Piper TTS model** — download `en_GB-alan-medium.onnx` + `en_GB-alan-medium.onnx.json` (~60 MB) from [HuggingFace rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_GB/alan/medium), place both files in `./voices/`, then set `PIPER_MODEL=voices/en_GB-alan-medium.onnx`.
>
> **Custom wake words:** `WAKE_WORDS=hades,jarvis` — comma-separated; fuzzy variants are auto-derived. `WAKE_DEBOUNCE=2.5` tunes echo protection.
>
> **Face auth:** set `FACE_AUTH_ENABLED=true` to require face verification on startup.

### 4. (Optional) Supabase cloud setup

Without Supabase, HADES stores memory in `conversation_history.json` and notes in `notes.txt`. With Supabase you get cloud-synced memory, multi-user support, and semantic (pgvector) search over past conversations.

1. Create a free project at [supabase.com](https://supabase.com)
2. Enable the `pgvector` extension in your Supabase project (Database → Extensions → vector)
3. Run `run_once_migrate_notes.py` once to create the required tables
4. Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to your `.env`

### 5. Run
```bash
python main.py
```

---

## Voice Commands

| Say... | Action |
|---|---|
| *"Hades"* | Wake up |
| *"What's the weather in London"* | Weather |
| *"Give me today's news"* | Top headlines |
| *"News about AI"* | Topic-specific news |
| *"What's Tesla's stock price"* | Stock price |
| *"What's Bitcoin at"* | Crypto price |
| *"Play Blinding Lights"* | Spotify song search |
| *"Play my liked songs"* | Spotify liked songs |
| *"Play my [name] playlist"* | Spotify playlist |
| *"Pause / skip / previous"* | Playback control |
| *"What's playing"* | Current track info |
| *"Shuffle"* | Toggle shuffle |
| *"Set volume to 60%"* | Volume control |
| *"Mute"* | Toggle mute |
| *"Open Chrome"* | Launch app |
| *"Open YouTube"* | Open website |
| *"Search for [query]"* | Google in browser |
| *"Take a screenshot"* | Screenshot to Desktop |
| *"What's on my screen"* | Groq Llama 4 Scout screen analysis |
| *"What's my clipboard"* | Read clipboard contents |
| *"What's my battery"* | Battery status |
| *"CPU / RAM / disk"* | System resource usage |
| *"What time is it"* | Current time |
| *"What's today"* | Current date |
| *"Shutdown in 30 minutes"* | Schedule shutdown |
| *"Restart"* | Restart PC |
| *"Lock"* | Lock workstation |
| *"Remind me in 10 minutes to eat"* | Timed reminder |
| *"Take a note: buy groceries"* | Save note (HADES asks for category) |
| *"Read my notes"* / *"Read my work notes"* | Read all notes or by category |
| *"Delete my last note"* | Remove most recent note |
| *"Delete my work notes"* | Delete all notes in a category |
| *"Clear memory"* | Reset conversation history |
| *"Help"* / *"Commands"* | Show the full command reference card |
| *"Goodbye" / "Sleep" / "Goodnight" / "Stand by"* | Enter sleep mode |

---

## Tech Stack

- **LLM:** Groq (LLaMA 3.3 70B Versatile) — free, fast inference
- **Screen Vision:** Groq (Llama 4 Scout 17B — multimodal)
- **Speech:** SpeechRecognition + Google STT
- **TTS:** PiperTTS (offline)
- **Cloud Memory:** Supabase + pgvector (optional)
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`) for semantic memory search
- **GUI:** PyWebview (animated holographic orb + chat log)
- **PC Control:** pyautogui, psutil, pycaw, pyperclip
- **APIs:** OpenWeatherMap, NewsAPI, Yahoo Finance, CoinGecko (all free)
- **Spotify:** Spotipy

---

## Project Structure

```
HADES/
├── main.py              # Entry point, voice loop, intent router
├── brain.py             # AI with local/Supabase memory
├── db.py                # Supabase client, embeddings, auth, notes, memory
├── voice.py             # Wake word detection, STT, TTS
├── commands.py          # PC control, notes, reminders, help card
├── gui.py               # Animated holographic GUI + auth flow
├── config.py            # .env loader
├── weather.py           # OpenWeatherMap API
├── news.py              # NewsAPI
├── stocks.py            # Yahoo Finance & CoinGecko
├── spotify.py           # Spotify control via Spotipy
├── vision.py            # Groq Llama 4 Scout screen analysis
├── face_auth.py         # Optional face recognition
├── run_once_migrate_notes.py  # One-time Supabase table creation
├── frontend/
│   └── index.html       # GUI frontend
├── voices/              # Piper TTS model files go here
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Memory Modes

| Mode | When active | How it works |
|---|---|---|
| **Local** | No Supabase configured | Last 20 turns stored in `conversation_history.json` |
| **Cloud** | Supabase configured + user logged in | Last 12 messages (recency) + top 5 semantically similar past turns via pgvector cosine search |

---

## License

MIT
