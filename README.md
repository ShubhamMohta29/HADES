# H.A.D.E.S — Human Assistance and Decision Engine System

A fully voice-activated AI assistant inspired by Iron Man's JARVIS, built with Python.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎙️ Wake Word | Say **"HADES"** to activate — no button needed |
| 🧠 AI Conversation | Powered by Groq LLaMA 3 with full memory |
| 🌤️ Weather | Real-time weather for any city |
| 📰 News | Top headlines or topic-specific news |
| 📈 Stocks & Crypto | Live prices via Yahoo Finance & CoinGecko |
| 🎵 Spotify | Play, pause, skip, search by voice |
| 🖥️ PC Control | Volume, apps, shutdown, lock, screenshots |
| 📝 Notes & Reminders | Voice-driven notes and timed reminders |
| 🔒 Face Auth | Optional face recognition login (OpenCV) |
| 🪟 GUI | Sleek dark-themed chat interface |

---

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/Jarvis.git
cd Jarvis
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

> **Note:** `face_recognition` requires cmake and dlib. On Windows:
> ```bash
> pip install cmake dlib face_recognition
> ```

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
| *"Play Blinding Lights"* | Spotify |
| *"Set volume to 60%"* | Volume control |
| *"Open Chrome"* | Launch app |
| *"Take a screenshot"* | Screenshot |
| *"Remind me in 10 minutes to eat"* | Reminder |
| *"Make a note: buy groceries"* | Save note |
| *"What's my battery"* | Battery status |
| *"Shutdown in 30 minutes"* | Schedule shutdown |
| *"Clear memory"* | Reset conversation |
| *"Goodbye"* | Go back to sleep |

---

## 🔒 Face Recognition (Optional)

Register your face:
```bash
python face_auth.py --register
```

Enable in `.env`:
```
FACE_AUTH_ENABLED=true
```

---

## 🛠️ Tech Stack

- **LLM:** Groq (LLaMA 3.1) — free, fast inference
- **Speech:** SpeechRecognition + Google STT
- **TTS:** pyttsx3 (offline)
- **GUI:** Tkinter
- **PC Control:** pyautogui, psutil, pycaw
- **APIs:** OpenWeatherMap, NewsAPI, Yahoo Finance, CoinGecko (all free)
- **Spotify:** Spotipy
- **Face Auth:** OpenCV + face_recognition

---

## 📁 Project Structure

```
Jarvis/
├── main.py          # Entry point + voice loop
├── brain.py         # AI with conversation memory
├── voice.py         # Wake word + STT + TTS
├── commands.py      # PC control commands
├── gui.py           # Chat window GUI
├── weather.py       # Weather API
├── news.py          # News API
├── stocks.py        # Stocks & crypto
├── spotify.py       # Spotify control
├── face_auth.py     # Face recognition
├── config.py        # API key loader
├── requirements.txt
└── .env.template
```

---

## 📄 License
MIT