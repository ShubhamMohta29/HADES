# H.A.D.E.S — Human Assistance and Decision Engineering System
A fully voice-activated AI assistant inspired by Iron Man's JARVIS, built with Python.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎙️ Wake Word | Say **"HADES"** to activate — no button needed |
| 😴 Sleep Mode | Say "sleep", "goodbye", etc. — mic stays on but only listens for wake word; orb dims |
| 🧠 AI Conversation | Powered by Groq LLaMA 3.3 70B with persistent memory |
| 🌤️ Weather | Real-time weather for any city |
| 📰 News | Top headlines or topic-specific news |
| 📈 Stocks & Crypto | Live prices via Yahoo Finance & CoinGecko |
| 🎵 Spotify | Play, pause, skip, search playlists & songs by voice |
| 🖥️ PC Control | Volume, apps, shutdown, lock, screenshots, clipboard |
| 👁️ Screen Vision | Ask HADES to look at your screen — powered by Groq Llama 4 Scout |
| 📝 Notes & Reminders | Voice-driven notes and timed reminders |
| 🪟 GUI | Animated holographic dark-themed interface |

---

## 🚀 Setup

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

| Key | Where to get it | Cost |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Free |
| `WEATHER_API_KEY` | [openweathermap.org/api](https://openweathermap.org/api) | Free |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) | Free |
| `SPOTIFY_*` | [developer.spotify.com](https://developer.spotify.com/dashboard) | Free |

> Set your default city: `DEFAULT_CITY`
>
> **Piper TTS model** — download `en_GB-alan-medium.onnx` + `en_GB-alan-medium.onnx.json` (~60 MB) from [HuggingFace rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_GB/alan/medium) and place both files in `./voices/`.
>
> Optional — `WAKE_WORDS=hades,jarvis` to add more wake words. `WAKE_DEBOUNCE=2.5` to tune echo protection.

### 4. Run
```bash
python main.py
```

---

## 🗣️ Voice Commands

| Say... | Action |
|---|---|
| *"Hades"* | Wake up |
| *"What's the weather in London"* | Weather |
| *"Give me today's news"* | Top headlines |
| *"What's Tesla's stock price"* | Stock price |
| *"What's Bitcoin at"* | Crypto price |
| *"Play Blinding Lights"* | Spotify song search |
| *"Play my liked songs"* | Spotify liked songs |
| *"Set volume to 60%"* | Volume control |
| *"Open Chrome"* | Launch app |
| *"Take a screenshot"* | Screenshot |
| *"What's on my screen"* | Groq Llama 4 Scout screen analysis |
| *"Remind me in 10 minutes to eat"* | Reminder |
| *"Take a note: buy groceries"* | Save note (HADES will ask which category) |
| *"Read my notes"* / *"Read my work notes"* | Read all notes or by category |
| *"help"* / *"commands"* | Show the full command reference card |
| *"What's my battery"* | Battery status |
| *"Shutdown in 30 minutes"* | Schedule shutdown |
| *"Clear memory"* | Reset conversation |
| *"Goodbye" / "Sleep" / "Goodnight" / "Stand by"* | Enter sleep mode — only wake word is heard |

---


## 🛠️ Tech Stack

- **LLM:** Groq (LLaMA 3.3 70B Versatile) — free, fast inference
- **Speech:** SpeechRecognition + Google STT
- **TTS:** PiperTTS (offline)
- **Vision:** Groq (Llama 4 Scout 17B — multimodal)
- **GUI:** PyWebview (animated holographic orb)
- **PC Control:** pyautogui, psutil, pycaw
- **APIs:** OpenWeatherMap, NewsAPI, Yahoo Finance, CoinGecko (all free)
- **Spotify:** Spotipy

---

## 📁 Project Structure

```
HADES/
├── main.py          # Entry point + voice loop + command router
├── brain.py         # AI with persistent conversation memory
├── voice.py         # Wake word + STT + TTS
├── commands.py      # PC control commands
├── gui.py           # Animated holographic GUI
├── weather.py       # Weather API
├── news.py          # News API
├── stocks.py        # Stocks & crypto
├── spotify.py       # Spotify control
├── vision.py        # Gemini screen analysis
├── face_auth.py     # Face recognition
├── config.py        # API key loader
├── frontend/
│   └── index.html
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 📄 License

MIT
