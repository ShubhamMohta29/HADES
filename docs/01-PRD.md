# Document 01 — PRD: Product Requirements Document

## App Name
**HADES** — Human Assistance and Decision Engineering System

## Tagline
A voice-first AI personal assistant that controls your PC, answers anything, and feels like JARVIS.

---

## Problem
Power users — developers, students, researchers — constantly switch between keyboard, mouse, and browser to do simple things: check the weather, look up a stock, control volume, open an app, or get a quick answer. There's no single, always-on, voice-first interface that ties all of these together with a personality. Existing smart assistants (Cortana, Siri) are shallow, cloud-locked, and feel corporate.

---

## Target User
A technically-inclined person (developer, student, or hobbyist) aged 18–30 who spends most of their day at a desktop or laptop. They're comfortable with Python and APIs, want their computer to feel like a sci-fi command center, and value speed and personality over generic polish. They've thought about building a JARVIS-style assistant before but never had a working starting point.

---

## Core Value Proposition
HADES is the only local-first, open-source AI assistant that combines a real conversational LLM (Groq Llama 70B), offline TTS, PC control, and a cinematic sci-fi UI — all in a single Python app that runs on any Windows machine.

---

## Core Features (Must Have)

- **Wake word detection** — Say "HADES" to activate; stays in standby otherwise
- **Voice input** — Microphone capture with Google STT; ambient noise adaptation
- **AI conversation** — Groq Llama 3.3 70B with persistent conversation history (trimmed to last 20 turns)
- **Offline TTS** — Piper neural TTS with a British male voice (JARVIS-feel)
- **Text input fallback** — Type commands in the GUI when mic isn't available
- **Weather** — Current weather by city via OpenWeatherMap
- **News** — Top headlines or topic-specific news via NewsAPI
- **Stocks & Crypto** — Live price lookup for stocks and top crypto coins
- **Spotify control** — Play, pause, skip, shuffle, query current track via Spotify API
- **PC control** — Volume, mute, time/date, battery, screenshot, clipboard, lock/shutdown/restart
- **App launcher** — Open Chrome, VS Code, Notepad, Calculator, Explorer, Office apps by voice
- **Website opener** — Open YouTube, GitHub, Gmail, Reddit, etc. by voice
- **System info** — CPU usage, RAM usage, disk space
- **Notes** — Save and read plain-text notes
- **Reminders** — Timed spoken reminders ("remind me in 10 minutes to...")
- **Web search** — Open a Google search in browser by voice
- **Screen vision** — Capture screen and analyze with Groq Llama 4 Scout (multimodal)
- **Memory reset** — "Clear memory" / "Forget everything" wipes conversation history
- **Sci-fi GUI** — Animated orb with status states (standby, listening, thinking, speaking)

---

## Nice to Have

- Face authentication (optional flag; OpenCV + face_recognition already wired)
- Calendar integration (read/create events)
- Email reading via Gmail API
- Smart home control (Philips Hue, etc.)
- Multi-language voice support
- Custom wake word training (replace Google STT wake word with offline Porcupine/Whisper)
- Hotkey to trigger without wake word
- Plugin system so users can drop in new skill modules
- Mobile companion app for remote access

---

## Out of Scope (v1)

- Multi-user support (one user per machine)
- Cloud sync of notes or conversation history
- Mobile app
- Any subscription or account system
- Sending emails or calendar events
- Web scraping beyond news/stock APIs

---

## User Stories

- As a user, I want to say "HADES" and have it respond immediately so that I can issue commands hands-free while coding.
- As a user, I want to ask about the weather so that I don't switch to a browser tab.
- As a user, I want to say "play some jazz" and have Spotify start so that I never interrupt my workflow.
- As a user, I want to say "take a note: refactor auth tomorrow" so that I capture thoughts without breaking focus.
- As a user, I want to ask "what's on my screen?" and get a helpful answer so that HADES can assist with anything visual.
- As a user, I want persistent conversation memory so that HADES remembers context across questions in a session.
- As a user, I want to say "clear memory" so that I can start a fresh conversation without restarting the app.
- As a user, I want a dark sci-fi UI so that the assistant feels like a proper command center, not a utility widget.

---

## Success Metrics

- App starts and wake word triggers within 5 seconds on a mid-range Windows machine
- Voice round-trip (wake → listen → think → speak) completes in under 4 seconds for conversational queries
- All documented commands work end-to-end without crashing
- TTS sounds natural (Piper offline model loaded and playing correctly)
- GUI status orb correctly reflects all four states: standby, listening, thinking, speaking
- Zero crashes in a 30-minute voice session
