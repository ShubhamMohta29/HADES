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
- **Wake word detection** — Neural model via `openwakeword` (local ONNX, no API, ~1 MB); falls back to fuzzy-STT polling if `openwakeword` is not installed or `NEURAL_WAKE_WORD=false`. Configurable via `WAKE_WORDS` / `WAKE_MODEL` env vars; debounce prevents echo double-fire
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
- **Note management** — Read notes by category; delete last note (immediate); delete category or all notes (requires spoken confirmation)
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
- **PC power** — Lock, shutdown (with delay), restart, cancel shutdown. Shutdown and restart require explicit spoken confirmation before executing; cancel-shutdown and lock execute immediately

### UI & Experience
- **Sci-fi GUI** — Animated orb with 6 status states (standby, sleeping, listening, followup, thinking, speaking)
- **Sleep mode** — Mic stays on but only wake word is processed; orb dims; distinct "I'm back, Sir" greeting on wake from sleep
- **Follow-up window** — After HADES replies, orb enters `followup` state (dimmed cyan) for up to `FOLLOWUP_TIMEOUT` seconds; user can ask follow-ups without re-saying the wake word; silence timeout returns to standby
- **Help command** — "help" / "commands" renders a styled command reference card in the chat log
- **Face authentication** — Optional face-recognition gate before voice loop; auto-registers on first run when no encodings are found (no manual `--register` step required); face encodings synced to Supabase `face_encodings` table (primary) and cached in `face_encodings.pkl` (local fallback); works cross-device when signed in

### Distribution & Setup
- **One-command installer** — `install.bat` creates venv, installs deps, downloads Piper binary and voice model, copies `.env.example`
- **Auto-download TTS model** — Piper voice model downloads automatically on first run if missing
- **Pre-flight smoke test** — `smoke_test.py` validates all configured API keys before first run
- **Pip-installable** — `setup.py` for development installs (`pip install -e .`)

---

## v1.0 — Shipped (Phases 14–16)

### Phase 14 — Neural Wake Word ✅
Replaced the fuzzy-STT polling loop with `openwakeword` — a local neural acoustic model that detects the wake phrase by scoring raw 16 kHz mic audio without transcribing every utterance. Eliminates false triggers from ambient speech and YouTube/TV audio. Falls back gracefully to the original STT polling loop if `openwakeword` is not installed or `NEURAL_WAKE_WORD=false`.

- **Config**: `WAKE_MODEL` (path to custom `.onnx`; empty = all built-in defaults), `NEURAL_WAKE_WORD` (bool, default `true`)
- **Files**: `voice/wake.py`, `requirements.txt`, `config.py`, `.env.example`

### Phase 15 — Continuous Conversation ✅
After HADES speaks, the mic stays open for up to `FOLLOWUP_TIMEOUT` seconds of silence. User can ask follow-ups without re-saying "HADES". The orb enters a new `followup` state (dimmed cyan, slower pulse). Silence timeout returns to standby with a system message. Sleep words still work during the window.

- **Config**: `FOLLOWUP_TIMEOUT` (seconds of silence before standby; default `15`)
- **UI**: new `followup` orb CSS state — `brightness(0.65)`, `hue-rotate(20deg)`, 2 s pulse, muted status color
- **Files**: `main.py`, `frontend/index.html`, `config.py`, `.env.example`

### Phase 16 — Action Confirmation Gate ✅
Destructive/irreversible actions (shutdown, restart, delete-all-notes, delete-category-notes) require explicit spoken confirmation. HADES asks "Are you sure, Sir?" — confirm words (`yes`, `confirm`, `go ahead`, …) execute the stored callable; deny words (`no`, `cancel`, …) cancel; `CONFIRM_TIMEOUT` seconds with no response auto-cancels. Required before shipping any write/send features in v1.5.

- **Config**: `CONFIRM_TIMEOUT` (seconds before auto-cancel; default `10`)
- **Pattern**: extends the existing `_pending_state` multi-turn machine in `router.py` with a new `"confirm_action"` action type
- **Files**: `router.py`, `config.py`, `.env.example`

---

## v1.1 — In Active Planning (Phases 17–20)

### Phase 17 — Streaming TTS
Groq responses begin playing as tokens arrive. Sentence-chunk the stream: buffer tokens until a natural boundary (`.`, `!`, `?`, or ≥ 6-word clause), hand each chunk to Piper immediately, play chunks sequentially. Perceived latency drops from 2–4 s to < 1 s on long answers.

- **Config**: `STREAMING_TTS` (bool, default `true`), `STREAM_CHUNK_MIN_WORDS` (int, default `6`)
- **Files**: `brain.py` (`think_stream()`), `voice/tts.py` (`speak_streaming()`), `main.py`, `config.py`

### Phase 18 — PyInstaller Distribution
Bundle HADES into a Windows `.exe` — no Python, pip, or venv required. Key challenges: pycaw COM interface generation, pywebview CEF engine, openwakeword ONNX runtime, Piper binary inclusion. `config.py` learns to resolve paths via `sys._MEIPASS` when frozen.

- **Deliverables**: `HADES.spec`, `build.bat`, documented bundle size
- **Files**: `HADES.spec`, `build.bat`, `config.py`

### Phase 19 — Action Log
A rolling local (and optional Supabase) log of every action HADES takes. "What did you do recently?" returns the last 5–10 entries as a spoken list. Required audit trail before shipping calendar write and email send in v1.5.

- **Config**: `ACTION_LOG_ENABLED` (bool, default `true`)
- **New module**: `action_log.py`; new Supabase table `action_log`; new `_ActionLogHandler` in `router.py`

### Phase 20 — Barge-in
Voice-activity detection (VAD) thread runs during TTS playback. When mic energy exceeds `VAD_THRESHOLD` for 2+ consecutive frames, an interrupt event fires, TTS stops between chunks, and the new speech is captured and routed normally. Depends on Phase 17 (streaming gives natural chunk seams).

- **Config**: `BARGE_IN_ENABLED` (bool, default `true`), `VAD_THRESHOLD` (int, default `500`)
- **New file**: `voice/vad.py`; modified `voice/tts.py`, `main.py`

---

## Nice to Have (v2.0+ roadmap)

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
- As a user, I want to ask follow-up questions without saying "HADES" again so a multi-turn conversation feels natural.
- As a user, I want HADES to ask "Are you sure?" before shutting down my computer so I never trigger it by accident.
- As a user, I want the wake word to fire reliably without false triggers from YouTube or TV audio playing in the background.
- As a user, I want HADES to start speaking within a second of asking a question so it feels instant, not like it's thinking.
- As a user, I want to say "stop" mid-sentence so I can interrupt and redirect without waiting for the full answer.
- As a user, I want to ask "what did you do recently?" so I can audit what HADES has opened, saved, or changed.
- As a user, I want to run HADES by double-clicking an exe so I can install it on a machine without setting up Python.

---

## Success Metrics

- App starts and wake word triggers within 5 seconds on a mid-range Windows machine
- Voice round-trip (wake → listen → think → speak) completes in under 4 seconds for conversational queries
- All documented commands work end-to-end without crashing
- TTS sounds natural (Piper offline model loaded and playing correctly)
- GUI status orb correctly reflects all six states: standby, sleeping, listening, followup, thinking, speaking
- Cloud memory: Supabase path stores and retrieves messages correctly; local fallback works when Supabase keys are absent
- Auth: session restores silently on app restart when token is valid; login panel shown when token is absent/expired
- Zero crashes in a 30-minute voice session
