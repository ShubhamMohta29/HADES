# Document 06 — Implementation Plan: Step-by-Step Build Sequence

> Current status: Core v1 is complete. This document reflects the full build sequence as-designed, and marks what is done vs. what remains.

---

## Phase 1: Project Setup ✅
**Goal**: Runnable skeleton with environment loading.

- [x] Create repo and `.gitignore` (exclude `.env`, `venv/`, `*.cache`, `conversation_history.json`, `notes.txt`, `voices/`)
- [x] Create `requirements.txt` with all dependencies
- [x] Create `config.py` — `dotenv` loader exposing all env var constants
- [x] Create `.env.example` with placeholder keys
- [x] Set up `venv` and verify `pip install -r requirements.txt` succeeds

**Done when**: `python -c "from config import GROQ_API_KEY; print('ok')"` runs without error.

---

## Phase 2: AI Brain ✅
**Goal**: Groq LLM conversation with persistent memory.

- [x] Implement `brain.py` — `think(user_input)` with full conversation history
- [x] Implement `load_memory()` / `save_memory()` — JSON file persistence
- [x] Implement `_trim()` — cap history at 20 turns
- [x] Implement `clear_memory()` — reset to system prompt only
- [x] Thread-safe lock on history mutations
- [x] Error handling for `GroqError` and unexpected exceptions (roll back user message)

**Done when**: `from brain import think; print(think("hello"))` returns a coherent reply.

---

## Phase 3: Voice I/O ✅
**Goal**: Working TTS and STT.

- [x] Implement `voice.py:speak(text)` — Piper TTS via Python API, fallback to CLI, fallback to print
- [x] Implement `voice.py:listen()` — SpeechRecognition microphone capture, returns transcript or None
- [x] Implement `voice.py:wait_for_wake_word()` — polling loop for "hades" with mishear tolerance
- [x] Handle `OSError` (no mic), `UnknownValueError` (silence), `WaitTimeoutError` (timeout)
- [ ] Place Piper voice model in `voices/en_GB-alan-medium.onnx` (download from huggingface.co/rhasspy/piper-voices — .onnx + .onnx.json, ~60 MB)

**Done when**: Script says something and mic input is transcribed correctly.

---

## Phase 4: GUI ✅
**Goal**: pywebview window with sci-fi orb UI, live chat log, and text input.

- [x] Implement `frontend/index.html` — full CSS layout, orb + rings + ticks, status area, chat div, input bar
- [x] Implement CSS state selectors (`body[data-status]`) for all four orb states
- [x] Implement JS functions: `addMessage()`, `addSystemMessage()`, `setStatus()`
- [x] Implement JS `sendText()` calling `window.pywebview.api.send_message(text)`
- [x] Implement `gui.py:HadesGUI` — pywebview window wrapper, `evaluate_js` helpers, `on_text_command` callback

**Done when**: Window opens, orb animates, chat messages appear, text input sends and receives a reply.

---

## Phase 5: PC Commands ✅
**Goal**: Voice/text control of Windows system functions.

- [x] Volume: set to %, volume up/down/mute (pycaw + pyautogui fallback) — `set_volume()` uses `getattr(speakers, '_dev', speakers)` to unwrap the AudioDevice wrapper introduced in newer pycaw versions before calling `Activate()` (Session 009 fix)
- [x] Time and date queries
- [x] Battery status (psutil)
- [x] Screenshot to Desktop (pyautogui)
- [x] Clipboard read (pyperclip)
- [x] Shutdown, restart, lock, cancel shutdown (os.system)
- [x] Notes: save and read (flat file)
- [x] Reminders: threaded timer + spoken alert
- [x] Web search (webbrowser + Google URL)
- [x] App launcher (subprocess.Popen for Chrome, VS Code, Notepad, etc.)
- [x] Website opener (webbrowser for YouTube, GitHub, Gmail, etc.)
- [x] System info: CPU, RAM, disk (psutil)

**Done when**: All listed commands tested by voice and text, returning correct responses.

---

## Phase 6: Info APIs ✅
**Goal**: Weather, news, stocks, crypto fetched and formatted.

- [x] `weather.py:get_weather(city)` — OpenWeatherMap, format as spoken sentence
- [x] `news.py:get_news(topic)` — NewsAPI, return top 5 headlines as spoken list
- [x] `stocks.py:get_stock(symbol)` — yfinance, return price + company name
- [x] `stocks.py:get_crypto(coin_id)` — CoinGecko, return price in USD

**Done when**: "What's the weather in Tokyo?", "Any news?", "Tesla stock", "Bitcoin price" all return useful answers.

---

## Phase 7: Spotify ✅
**Goal**: Voice-controlled Spotify playback.

- [x] `spotify.py` — spotipy OAuth setup, handle scope
- [x] Commands: play by query, pause, resume, skip, previous, shuffle, current track
- [x] Detect active device; surface friendly error if Spotify is not open
- [x] Trigger phrases wired into `main.py:route()` before PC commands

**Done when**: "Play some jazz", "Skip song", "What's playing?" work with Spotify open.

---

## Phase 8: Screen Vision ✅
**Goal**: Screenshot + Groq multimodal analysis on voice trigger.

- [x] `vision.py:analyze_screen(prompt)` — ImageGrab, resize, base64 encode, Groq Llama 4 Scout
- [x] Trigger phrases wired into `main.py:route()` (checked before weather/news to avoid collision)
- [x] Handle rate limit error gracefully

**Done when**: "What's on my screen?" returns a description of the current screen content.

---

## Phase 9: Intent Router & Main Loop ✅
**Goal**: Full voice loop with correct priority routing.

- [x] `main.py:route()` — priority chain: memory reset → screen → weather → news → stocks → crypto → Spotify → PC commands → LLM fallback
- [x] `main.py:hades_loop()` — outer standby loop + inner listening loop
- [x] GUI status updates at each stage (listening → thinking → speaking → standby)
- [x] "sleep"/"goodbye"/"stand by" exits inner loop back to wake word detection
- [x] Exception handling in main loop — log and continue, never crash

**Done when**: Full voice session works end-to-end for all command categories without crashing.

---

## Phase 10: Face Auth (Optional) ✅
**Goal**: Optional face gate before activating voice loop.

- [x] `face_auth.py:verify_face()` — capture frame, compare against `known_faces/`
- [x] `FACE_AUTH_ENABLED` flag in `.env` / `config.py`
- [x] Gate wired into `hades_loop()` before `wait_for_wake_word()`

**Done when**: With `FACE_AUTH_ENABLED=true`, unrecognized face is denied; known face passes through.

---

## Phase 11: Polish & Hardening ✅
**Goal**: Reliability, error coverage, and user experience refinements.

- [x] README with full setup instructions (API keys, Piper model download, venv setup)
- [x] Graceful mic handling — `MIC_ERROR` sentinel in `listen()`; 3 consecutive failures show GUI warning and switch to text-only; reconnect is detected and announced
- [x] Configurable wake words via `.env` (`WAKE_WORDS=hades,jarvis`); per-word fuzzy STT-mishear variant sets; generic fallback rules for unknown words
- [x] Debounce rapid double-wake-word triggers (`WAKE_DEBOUNCE=2.5` seconds, configurable)
- [x] Spotify errors summarized by HTTP status code into 1–2 spoken sentences; raw exception logged only
- [x] `help` / `commands` voice or text command — GUI renders a dedicated styled help card; HADES speaks a short intro only
- [x] Notes with optional category tagging — conversational flow: HADES asks which category, uses LLM to suggest the best fit, user confirms or names a different one; `read my [category] notes` filters by tag
- [x] Test suite for `route()` logic — 24 unit tests in `tests/test_route.py`; all dependencies mocked; runs with `pytest tests/`

**Bonus fix (caught by tests)**: Stock routing regex now handles both `"Tesla stock"` and `"stock Tesla"` word orders.

---

## Phase 12: Distribution ✅
**Goal**: Make it easy for others to install and run.

- [x] `setup.py` for pip-installable packaging (`pip install -e .`; entry point `hades = main:main`)
- [ ] GitHub Releases with bundled Windows `.exe` (PyInstaller) — deferred to post-v1.0
- [x] Auto-download Piper voice model on first run if not present (`voice.py:_auto_download_piper()`)
- [x] One-command install script (`install.bat` — creates venv, installs deps, downloads Piper binary + voice model, copies `.env.example`)

---

## Phase 13: Supabase Cloud Memory & Auth ✅
**Goal**: Cloud-synced multi-user memory with semantic search; user authentication.

- [x] Create Supabase project; run `supabase_schema.sql` (pgvector, tables, RLS, `match_memory` function)
- [x] Add `SUPABASE_URL` + `SUPABASE_ANON_KEY` to `.env` and `.env.example`
- [x] Install `supabase` and `sentence-transformers` Python packages
- [x] Write `db.py` — centralised Supabase client: `is_available()`, `embed()`, auth helpers, notes CRUD, memory read/write/search
- [x] Add login UI to `gui.py` — login panel with email+password, magic link, skip; session persisted in `~/.jarvis/session.json`; silent restore on restart
- [x] Refactor `brain.py` — two-tier memory: `load_recent(user_id, n=12)` + `retrieve_relevant(user_id, query, k=5)`; falls back to local JSON when Supabase absent
- [x] Refactor `commands.py` — notes functions (`save_note`, `read_notes`, `get_existing_categories`, `delete_last_note`, `delete_notes`) all db-aware via `_use_db(user_id)` helper
- [x] Thread `user_id` through `main.py` — `on_auth_complete` callback; `hades_loop()` and `handle_text_command()` both pass `user_id` to `route()`
- [x] Add note deletion to `route()` — three regex branches (last note, by category, all notes) mapped to `commands.delete_last_note` / `commands.delete_notes`
- [x] Write `run_once_migrate_notes.py` — one-time import of `notes.txt` into Supabase; preserves timestamps + category tags; renames file to `.bak`
- [x] Write `smoke_test.py` — pre-flight API key validation for Groq, OpenWeatherMap, NewsAPI, Spotify, Supabase (auth endpoint + schema table existence check for `notes` and `conversation_memory`)
- [x] Write `supabase_schema.sql` — SQL file for Supabase SQL editor (tables, RLS, `match_memory` function)
- [x] Remove `google-generativeai` from `requirements.txt` (unused since vision migrated to Groq in Session 001)
- [x] Update `.gitignore` — add `face_encodings.pkl`, `notes.txt.bak`
- [x] Full README rewrite — install.bat path, Supabase setup with schema.sql, smoke test, face registration, Piper auto-download

**Done when**: Supabase-configured run stores messages and retrieves semantic matches; local-mode run works identically to pre-Supabase with flat files.

---

## Done Criteria (v0.x Shipped ✅)

- [x] All Phase 1–13 items checked off
- [x] `.env.example` documents every required key
- [x] `README.md` covers install, setup, and first-run steps
- [x] `smoke_test.py` validates all configured API keys
- [x] `install.bat` one-command setup for Windows
- [ ] App starts cold in under 10 seconds *(target for v1.0 with streaming)*
- [ ] Wake word triggers reliably in a quiet room *(neural wake word — v1.0)*
- [ ] No unhandled exceptions in a 30-minute voice session *(manual QA — ongoing)*
- [ ] PyInstaller `.exe` bundle for distribution without Python *(v1.0)*

**v1.0 goals** — see README Roadmap: continuous conversation, barge-in, streaming TTS, neural wake word, action confirmation gate.

---

## Phase 14: Neural Wake Word ⬜ (next)
**Goal**: Replace fuzzy-STT wake word polling with a local neural acoustic model. Eliminates false triggers, reduces CPU load during standby, and is a prerequisite for the continuous conversation window (Phase 15).

**Library**: [`openwakeword`](https://github.com/dscripka/openWakeWord) — free, local, no API key. Uses a small neural model (~1 MB) that runs on the mic stream without transcribing speech.

- [ ] Add `openwakeword` to `requirements.txt`
- [ ] Add `WAKE_MODEL` env var to `config.py` and `.env.example` — path to custom `.onnx` wake word model; defaults to the built-in "hey jarvis" or a HADES-trained model
- [ ] Rewrite `voice.py:wait_for_wake_word()` — swap STT polling loop for `openwakeword.Model` streaming inference on raw mic audio; keep `WAKE_DEBOUNCE` logic; keep `listen_for_wake_word_once()` helper using the same model
- [ ] Remove or demote the old fuzzy-STT fallback (keep as a `--no-neural` flag for debugging)
- [ ] Test: reliable detection at 1m distance in quiet room; < 2 false triggers per hour of ambient speech

**Done when**: "HADES" is detected consistently without false-triggering on "Hades" in a YouTube video playing in the background.

---

## Phase 15: Continuous Conversation ⬜ (next, after Phase 14)
**Goal**: After HADES speaks its reply, keep the mic open for a follow-up window instead of returning to standby. User can ask "what about Tuesday?" without re-saying the wake word — this is the core JARVIS feel missing from the current loop.

- [ ] Add `FOLLOWUP_TIMEOUT` env var to `config.py` and `.env.example` (default: `15` seconds)
- [ ] Refactor `main.py:hades_loop()` inner loop — after `speak(response)`, instead of returning to `wait_for_wake_word()`, continue the `listen()` loop for up to `FOLLOWUP_TIMEOUT` seconds of silence before breaking back to standby
- [ ] Display a "follow-up" orb sub-state in the GUI (listening state with a subtle countdown indicator or dimming effect) so the user knows the window is open
- [ ] Exit the follow-up window on: explicit sleep word, `FOLLOWUP_TIMEOUT` seconds of consecutive silence, or `MIC_ERROR` streak
- [ ] Handle text commands: `handle_text_command()` already works regardless of voice state; no change needed
- [ ] Test: three consecutive follow-up questions work without re-waking; timeout returns to standby correctly; sleep word during follow-up window enters sleep (not standby)

**Done when**: A 5-turn conversation ("HADES" → Q1 → A1 → Q2 → A2 → Q3 → A3 → silence → standby) completes without the user re-saying the wake word.

---

## Phase 16: Action Confirmation Gate ⬜ (after Phase 15)
**Goal**: Destructive or irreversible actions require an explicit spoken or clicked confirmation before executing. This is a safety prerequisite before shipping calendar write and email send features (v1.5).

**Actions requiring confirmation**: shutdown, restart, delete all notes, delete category notes, (future) send email, (future) create/delete calendar event.

- [ ] Add `_confirm_pending` state to `_pending_state` dict in `main.py` — similar to the note-category flow; stores the deferred action callable + description
- [ ] Add `_CONFIRM_WORDS` frozenset (e.g. "yes", "confirm", "do it", "go ahead") and `_DENY_WORDS` (e.g. "no", "cancel", "stop", "never mind") to `main.py`
- [ ] Add `_handle_confirm_state(t)` in `main.py` — if `_confirm_pending` is active, check confirm/deny; on confirm, call the stored callable; on deny or ambiguous, cancel and say "Cancelled, Sir."
- [ ] Wrap destructive commands in `commands.py` with a `requires_confirm` marker (simple dict or decorator) so `route()` can intercept them before execution
- [ ] In `route()`: when a destructive command is matched, instead of calling it immediately, set `_confirm_pending` and return the confirmation prompt ("Are you sure you want to shut down, Sir?")
- [ ] GUI: show the confirmation prompt in the chat + orb stays in THINKING state until resolved
- [ ] Add `CONFIRM_TIMEOUT` env var (default: `10s`) — if no response within timeout, auto-cancel
- [ ] Test: "shutdown" → "Are you sure?" → "yes" → shuts down; "shutdown" → "no" → "Cancelled, Sir."; timeout → auto-cancel

**Done when**: All destructive commands require confirmation; confirmation state clears correctly on sleep word, timeout, and denial.
