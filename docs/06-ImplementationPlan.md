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

- [x] `router.py:route()` — priority chain: memory reset → screen → weather → news → stocks → crypto → Spotify → PC commands → LLM fallback *(later refactored to Strategy pattern — see Phase 13.5)*
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
- [x] Refactor `commands/notes.py` — notes functions (`save_note`, `read_notes`, `get_existing_categories`, `delete_last_note`, `delete_notes`) all db-aware via `_use_db(user_id)` helper
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

## Phase 13.5: Architectural Refactor — Package Restructure + Strategy Pattern ✅
**Goal**: Apply SOLID principles (SRP, OCP) and the Strategy design pattern (GoF §12.3.1) to eliminate monolithic if-elif chains and prepare the codebase for extensibility.

**Session 010 — Package restructure** (SRP):
- [x] Split flat `voice.py` → `voice/` package (`tts.py`, `stt.py`, `wake.py`, `__init__.py`)
- [x] Split flat `commands.py` → `commands/` package (`system.py`, `notes.py`, `help.py`, `__init__.py`)
- [x] Move service modules into `services/` package (`weather.py`, `news.py`, `stocks.py`, `spotify.py`)
- [x] Extract intent routing from `main.py` into a standalone `router.py`
- [x] Delete stale flat files: `commands.py`, `voice.py`, `weather.py`, `news.py`, `stocks.py`, `spotify.py`
- [x] All 24 existing tests pass with zero changes

**Session 011 — Strategy pattern** (OCP):
- [x] Rewrite `router.py` — 70-line if-elif in `route()` replaced by 11 `_Handler` subclasses + `_HANDLERS` registry; `route()` reduced to a 10-line dispatcher loop
- [x] Rewrite `commands/system.py` — 112-line if-elif in `handle_command()` replaced by 12 `_CommandHandler` subclasses + `_COMMAND_HANDLERS` registry; `handle_command()` = 6-line dispatcher
- [x] Fix pre-existing cancel-shutdown bug: "cancel shutdown" was unreachable because "shutdown" matched first; fixed by checking "cancel shutdown" before "shutdown" in `_PowerHandler.handle()`
- [x] Pre-compile handler regexes at class-definition time (not per-call)
- [x] All 24 tests pass with zero changes — handler methods resolve module-level names at call time, preserving all `patch("router.xxx")` patches

**Done when**: `pytest tests/` passes 24/24; `route()` and `handle_command()` are each ≤ 10 lines; adding a new intent or command requires only a new subclass + list append, not modifying the dispatcher.

---

## Done Criteria (v1.0 Core Shipped ✅)

- [x] All Phase 1–16 items checked off
- [x] `.env.example` documents every required key including Phases 14–16 vars
- [x] `README.md` covers install, setup, and first-run steps
- [x] `smoke_test.py` validates all configured API keys
- [x] `install.bat` one-command setup for Windows
- [x] Wake word triggers via neural model (openwakeword) with STT fallback
- [x] Continuous conversation — follow-up window open after every reply
- [x] Confirmation gate — destructive actions (shutdown, restart, delete notes) ask before executing
- [x] 33 unit tests for `router.route()`, all passing
- [ ] App starts cold in under 10 seconds *(target for v1.1 with streaming)*
- [ ] No unhandled exceptions in a 30-minute voice session *(manual QA — ongoing)*
- [ ] PyInstaller `.exe` bundle for distribution without Python *(v1.1)*

**v1.1 goals** — barge-in, streaming TTS, PyInstaller distribution.
**v1.5 goals** — calendar integration, email assistant (requires confirm gate ✅ already done).

---

## Phase 14: Neural Wake Word ✅
**Goal**: Replace fuzzy-STT wake word polling with a local neural acoustic model. Eliminates false triggers, reduces CPU load during standby, and is a prerequisite for the continuous conversation window (Phase 15).

**Library**: [`openwakeword`](https://github.com/dscripka/openWakeWord) — free, local, no API key. Uses a small neural model (~1 MB) that runs on the mic stream without transcribing speech.

- [x] Add `openwakeword` to `requirements.txt`
- [x] Add `WAKE_MODEL` env var to `config.py` and `.env.example` — path to custom `.onnx` wake word model; empty = load all built-in default models
- [x] Add `NEURAL_WAKE_WORD` boolean env var to `config.py` and `.env.example` (default: `true`); set to `false` to force STT fallback for debugging
- [x] Rewrite `voice/wake.py` — dual-path: if `openwakeword` is installed and `NEURAL_WAKE_WORD=true`, stream 16 kHz raw mic audio through `openwakeword.Model` (lazy singleton, score > 0.5 threshold); otherwise fall back to the original STT polling loop; both paths respect `WAKE_DEBOUNCE`
- [x] Neural path uses `pyaudio` directly (1280-sample chunks at 16 kHz); stream opened/closed per call
- [x] Exception in neural path falls back to STT rather than crashing

**Done when**: `openwakeword` installed → neural path; not installed → STT fallback; `NEURAL_WAKE_WORD=false` → STT fallback. `listen_for_wake_word_once()` also dispatches to the correct path.

---

## Phase 15: Continuous Conversation ✅
**Goal**: After HADES speaks its reply, keep the mic open for a follow-up window instead of returning to standby. User can ask "what about Tuesday?" without re-saying the wake word — this is the core JARVIS feel missing from the current loop.

- [x] Add `FOLLOWUP_TIMEOUT` env var to `config.py` and `.env.example` (default: `15` seconds)
- [x] Refactor `main.py:hades_loop()` inner loop — after `speak(response)`, set `_in_followup = True` and `_followup_silence_start = time.time()`; continue the `listen()` loop; on each silence (`None` return), check if elapsed silence exceeds `FOLLOWUP_TIMEOUT`; if so, break to standby with a system message
- [x] Each new utterance resets the silence timer (`_in_followup = True`, `_followup_silence_start` updated)
- [x] GUI shows new `followup` orb state during the window — dimmer cyan (65% brightness, hue-rotated 20°, slower 2 s pulse) + muted status color `#00a8c0`; CSS added to `frontend/index.html`
- [x] Exit conditions: sleep word → sleep mode; `FOLLOWUP_TIMEOUT` seconds of silence → standby; `MIC_ERROR` streak still triggers text-only warning; text commands unaffected

**Done when**: A 5-turn conversation ("HADES" → Q1 → A1 → Q2 → A2 → Q3 → A3 → silence → standby) completes without the user re-saying the wake word.

---

## Phase 16: Action Confirmation Gate ✅
**Goal**: Destructive or irreversible actions require an explicit spoken or clicked confirmation before executing. This is a safety prerequisite before shipping calendar write and email send features (v1.5).

**Actions requiring confirmation**: shutdown, restart, delete all notes, delete category notes.

- [x] Add `CONFIRM_TIMEOUT` env var to `config.py` and `.env.example` (default: `10` seconds) — auto-cancels unconfirmed actions
- [x] Add `_CONFIRM_WORDS` frozenset (`yes`, `yeah`, `yep`, `confirm`, `do it`, `go ahead`, `proceed`, `sure`, `affirmative`) and `_DENY_WORDS` (`no`, `nope`, `cancel`, `stop`, `abort`, `never mind`, `nevermind`, `don't`, `dont`) to `router.py`
- [x] Add `_handle_confirm_state(lower)` in `router.py` — checks timeout, confirm words, deny words; on confirm calls the stored callable; on deny returns "Cancelled, Sir."; on ambiguous re-prompts once
- [x] Extend `_handle_pending_state()` — dispatches to `_handle_confirm_state()` when `action == "confirm_action"` (alongside existing `"save_note"` path)
- [x] Add `_PowerConfirmHandler` in `router.py` — registered before `_PCCommandHandler`; intercepts `shutdown`/`shut down`/`restart` (skips if "cancel" is present); stores `functools.partial(handle_command, text)` as deferred callable in `_pending_state`; "cancel shutdown" and "lock" pass through to `_PCCommandHandler` unchanged
- [x] Update `_DeleteNoteHandler` in `router.py` — "delete last note" still executes immediately; "delete all notes" and "delete [category] notes" now set `_confirm_pending` with `functools.partial(delete_notes, ...)` as the deferred callable
- [x] Add 9 new tests in `tests/test_route.py` covering: shutdown prompt, restart prompt, cancel-shutdown bypass, yes-execute, no-cancel, timeout auto-cancel, delete-all prompt, delete-category prompt, delete-last no-confirm; total test count: **33**
- [x] Add `_cfg.CONFIRM_TIMEOUT = 10.0` to the test stub config so numeric comparisons work correctly

**Done when**: All 33 tests pass; shutdown/restart/delete-all/delete-category require confirmation; delete-last and cancel-shutdown do not; timeout auto-cancels cleanly.
