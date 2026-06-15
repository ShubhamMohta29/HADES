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
HADES is the only local-first, open-source AI assistant that combines a real conversational LLM (Groq Llama 70B), offline TTS, PC control, optional cloud memory with semantic search, and a cinematic sci-fi UI — all in a single Python app that runs on any Windows machine.

---

## Core Features (Shipped)

### Conversation & Memory
- **Wake word detection** — Say "HADES" to activate; stays in standby otherwise. Configurable via `WAKE_WORDS` env var; debounce prevents echo double-fire
- **Voice input** — Microphone capture with Google STT; ambient noise adaptation; MIC_ERROR sentinel enables graceful text-only fallback after 3 consecutive failures
- **AI conversation** — Groq Llama 3.3 70B with persistent memory (see Cloud Memory below)
- **Cloud memory** — Optional Supabase backend; two-tier: last 12 turns (recency) + top 5 semantically relevant past turns via pgvector cosine search (all-MiniLM-L6-v2 embeddings). Falls back to local JSON (last 20 turns) when Supabase is not configured
- **Multi-user authentication** — Email+password or magic link via Supabase Auth; session persisted in `~/.jarvis/session.json` and restored automatically on restart; skip option for single-user local mode
- **Text input fallback** — Type commands in the GUI when mic isn't available
- **Memory reset** — "Clear memory" wipes conversation history (Supabase or local)

### Information & Knowledge
- **Weather** — Current weather by city via OpenWeatherMap
- **News** — Top headlines or topic-specific news via NewsAPI
- **Stocks & Crypto** — Live price lookup (yfinance + CoinGecko)
- **Screen vision** — Capture screen and analyze with Groq Llama 4 Scout (multimodal); same API key as conversation, no extra cost

### Productivity
- **Notes** — Save voice notes with optional category tagging; conversational flow (HADES suggests a category using LLM, user confirms)
- **Note management** — Read notes by category; delete last note; delete all notes in a category
- **Reminders** — Timed spoken reminders ("remind me in 10 minutes to...")

### PC Control
- **Spotify control** — Play, pause, skip, shuffle, query current track via Spotify API
- **Volume** — Set to %, volume up/down/mute
- **System info** — CPU usage, RAM usage, disk space, battery status, time/date
- **Screenshot** — Save to Desktop
- **Clipboard** — Read clipboard contents aloud
- **App launcher** — Open Chrome, VS Code, Notepad, Calculator, Explorer, Office apps by voice
- **Website opener** — Open YouTube, GitHub, Gmail, Reddit, etc. by voice
- **Web search** — Open Google search in browser by voice
- **PC power** — Lock, shutdown (with delay), restart, cancel shutdown

### UI & Experience
- **Sci-fi GUI** — Animated orb with 5 status states (standby, sleeping, listening, thinking, speaking)
- **Sleep mode** — Mic stays on but only wake word is processed; orb dims; distinct "I'm back, Sir" greeting on wake from sleep
- **Help command** — "help" / "commands" renders a styled command reference card in the chat log
- **Face authentication** — Optional face-recognition gate before voice loop; register with `python face_auth.py --register`

### Distribution & Setup
- **One-command installer** — `install.bat` creates venv, installs deps, downloads Piper binary and voice model, copies `.env.example`
- **Auto-download TTS model** — Piper voice model downloads automatically on first run if missing
- **Pre-flight smoke test** — `smoke_test.py` validates all configured API keys before first run
- **Pip-installable** — `setup.py` for development installs (`pip install -e .`)

---

## v1.0 — In Active Planning (Phases 14–16)

### Phase 14 — Neural Wake Word
Replace the current fuzzy-STT polling loop with `openWakeWord` — a local neural acoustic model (~1 MB) that detects the wake phrase without transcribing every utterance. Eliminates false triggers from ambient speech and YouTube/TV audio. Lower CPU in standby. Required before relaxing the conversation loop (Phase 15).

- **Input**: raw mic audio stream
- **Output**: wake event (probability > threshold)
- **Config**: `WAKE_MODEL` env var for custom `.onnx` model path; built-in HADES model as default
- **Files**: `voice/wake.py`, `requirements.txt`, `config.py`, `.env.example`

### Phase 15 — Continuous Conversation
After HADES speaks, keep the mic open for a configurable window (default 15s) instead of returning to standby. User can ask follow-ups without re-saying "HADES". Silence timeout or sleep-word exits the window. Depends on Phase 14 for reliable detection.

- **Config**: `FOLLOWUP_TIMEOUT` env var (seconds of silence before standby)
- **UI**: subtle orb state during follow-up window (listening, slightly dimmed)
- **Files**: `main.py`, `config.py`, `.env.example`

### Phase 16 — Action Confirmation Gate
Destructive/irreversible actions (shutdown, restart, delete-all-notes, future: send email, delete calendar event) require explicit spoken or clicked confirmation. HADES asks "Are you sure, Sir?" — "yes/confirm" proceeds; anything else cancels. Timeout auto-cancels. Required before shipping any write/send features in v1.5.

- **Pattern**: reuses `_pending_state` multi-turn machine already in `router.py`
- **Files**: `router.py`, `commands/system.py`

---

## Nice to Have (Planned — later roadmap)

- Barge-in / interruptible speech
- Streaming TTS responses
- Calendar integration (Google Calendar read/create)
- Email assistant (Gmail; sends only after confirmation)
- Morning/evening briefings (proactive digest)
- Smart home control (Home Assistant bridge)
- Web research agent (search, open, summarize)
- Document/PDF Q&A
- Plugin/skill system
- Mobile companion app
- Offline LLM (Ollama backend)
- Speaker identification

---

## Out of Scope (v0.x)

- Sending emails or calendar events autonomously (requires action confirmation gate — v1.0)
- Web scraping beyond news/stock APIs (v2.0 web research agent)
- Mobile app (v2.0 companion)
- Subscription or account system (Supabase is the auth layer; no HADES-specific accounts)

---

## User Stories

- As a user, I want to say "HADES" and have it respond immediately so I can issue commands hands-free while coding.
- As a user, I want to ask about the weather so I don't have to switch to a browser tab.
- As a user, I want to say "play some jazz" and have Spotify start so I never interrupt my workflow.
- As a user, I want to say "take a note: refactor auth tomorrow" so I capture thoughts without breaking focus.
- As a user, I want to say "delete my last note" so I can remove accidental saves by voice.
- As a user, I want to ask "what's on my screen?" and get a helpful answer so HADES can assist with anything visual.
- As a user, I want persistent conversation memory so HADES remembers context across questions in a session and across sessions (cloud mode).
- As a user, I want to say "clear memory" so I can start a fresh conversation without restarting the app.
- As a user, I want to log in with my email so my notes and memory are synced across restarts and machines.
- As a user without a Supabase account, I want to skip login and run locally so there's no mandatory cloud dependency.
- As a user, I want to run `smoke_test.py` before starting so I know all my API keys are valid.
- As a user, I want a dark sci-fi UI so the assistant feels like a proper command center, not a utility widget.

---

## Success Metrics

- App starts and wake word triggers within 5 seconds on a mid-range Windows machine
- Voice round-trip (wake → listen → think → speak) completes in under 4 seconds for conversational queries
- All documented commands work end-to-end without crashing
- TTS sounds natural (Piper offline model loaded and playing correctly)
- GUI status orb correctly reflects all five states: standby, sleeping, listening, thinking, speaking
- Cloud memory: Supabase path stores and retrieves messages correctly; local fallback works when Supabase keys are absent
- Auth: session restores silently on app restart when token is valid; login panel shown when token is absent/expired
- Zero crashes in a 30-minute voice session
