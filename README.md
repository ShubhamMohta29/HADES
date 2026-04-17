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
| 🧠 AI Conversation | Powered by Groq LLaMA 3.1 with persistent memory |
| 🌤️ Weather | Real-time weather for any city |
| 📰 News | Top headlines or topic-specific news |
| 📈 Stocks & Crypto | Live prices via Yahoo Finance & CoinGecko |
| 🎵 Spotify | Play, pause, skip, search playlists & songs by voice |
| 🖥️ PC Control | Volume, apps, shutdown, lock, screenshots, clipboard |
| 👁️ Screen Vision | Ask HADES to look at your screen — powered by Gemini |
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
cp .env.template .env
```

Edit `.env` with your keys:

| Key | Where to get it | Cost |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Free |
| `WEATHER_API_KEY` | [openweathermap.org/api](https://openweathermap.org/api) | Free |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) | Free |
| `SPOTIFY_*` | [developer.spotify.com](https://developer.spotify.com/dashboard) | Free |

> Set your default city: `DEFAULT_CITY`

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
| *"What's Bitcoin at"* | Crypto price | *In Progress*
| *"Play Blinding Lights"* | Spotify song search |
| *"Play my liked songs"* | Spotify liked songs |
| *"Set volume to 60%"* | Volume control |
| *"Open Chrome"* | Launch app |
| *"Take a screenshot"* | Screenshot |
| *"What's on my screen"* | Gemini screen analysis |
| *"Remind me in 10 minutes to eat"* | Reminder |
| *"Make a note: buy groceries"* | Save note |
| *"Read my notes"* | Read notes back |
| *"What's my battery"* | Battery status |
| *"Shutdown in 30 minutes"* | Schedule shutdown |
| *"Clear memory"* | Reset conversation |
| *"Goodbye"* | Go back to sleep |

---


## 🛠️ Tech Stack

- **LLM:** Groq (LLaMA 3.1 8B) — free, fast inference
- **Speech:** SpeechRecognition + Google STT
- **TTS:** PiperTTS (offline)
- **Vision:** Groq (LLaMA 3.1 8B)
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
