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
**Goal**: Optional face gate before activating voice loop; Supabase-synced encodings; auto-registration on first run.

- [x] `face_auth.py:verify_face(user_id)` — load encodings (Supabase first, local `.pkl` fallback); if none found, auto-register; capture frames and compare against stored encodings
- [x] `face_auth.py:register_face(user_id)` — capture 30 webcam frames; save encodings to `face_encodings.pkl` and Supabase `face_encodings` table
- [x] `FACE_AUTH_ENABLED` flag in `.env` / `config.py`
- [x] Gate wired into `hades_loop()` before `wait_for_wake_word()`; `user_id` passed from `main.py`
- [x] `db.save_face_encodings(user_id, encodings)` / `db.load_face_encodings(user_id)` — upsert/read from `face_encodings` Supabase table
- [x] `face_encodings` table added to `scripts/supabase_schema.sql` with RLS

**Done when**: With `FACE_AUTH_ENABLED=true`, first run auto-registers; subsequent runs verify without manual setup; encodings sync to Supabase so cross-device re-registration is not needed; unrecognized face is denied.

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

**v1.1 goals** — Phases 17–20: streaming TTS, PyInstaller distribution, action log, barge-in.
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

---

## Phase 17: Streaming TTS ⬜ (next)
**Goal**: Begin speaking as Groq tokens arrive instead of waiting for the full response. Cuts perceived latency by 1–3 seconds on long answers — the single most noticeable UX improvement remaining.

**Strategy**: sentence-chunk the Groq stream. Buffer incoming tokens until a natural speech boundary (`.`, `!`, `?`, `—`, or clause of ≥ 8 words ending a phrase); hand each chunk to Piper TTS immediately; play chunks sequentially. The user hears the first words within ~500 ms of Groq starting to respond.

- [ ] Add `STREAMING_TTS` boolean env var to `config.py` and `.env.example` (default: `true`); `false` falls back to the current full-response path for debugging
- [ ] Add `brain.py:think_stream(user_input, user_id)` — calls Groq with `stream=True`; yields sentence-boundary-split text chunks as they arrive; accumulates full response for memory storage after streaming ends; same memory lookup and history management as `think()`
- [ ] Add `voice/tts.py:speak_streaming(chunks)` — accepts an iterable of text strings; for each chunk, calls the existing Piper render path and appends audio to the playback queue; non-blocking between chunks so the next chunk renders while the previous plays
- [ ] Refactor `main.py:hades_loop()` — if `STREAMING_TTS`, call `think_stream()` + `speak_streaming()` together; orb transitions from `thinking` to `speaking` on first audio chunk rather than after the full response
- [ ] `handle_text_command()` uses the same streaming path; GUI receives incremental `addMessage` calls so the chat log updates word-by-word (optional — can batch at sentence boundaries instead)
- [ ] Graceful fallback: if the streaming path raises any exception mid-stream, catch it and speak whatever has been accumulated so far; log the truncation
- [ ] Add `STREAM_CHUNK_MIN_WORDS` env var (default: `6`) — minimum word count before a chunk is dispatched to TTS; prevents sending single-word fragments that produce choppy audio
- [ ] Test: voice round-trip perceived latency < 2 s for a 3-sentence response; streaming and non-streaming (`STREAMING_TTS=false`) produce identical final spoken text; no audio glitches between chunks

**Done when**: "What's the weather in Tokyo?" response begins playing within 1 second of Groq starting to stream; the full sentence count is preserved; `STREAMING_TTS=false` works as before.

---

## Phase 18: PyInstaller Distribution ⬜
**Goal**: Bundle HADES into a single Windows `.exe` so users can run it without installing Python, pip, or a virtual environment. Required for any wider distribution.

**Key challenge**: HADES has many C-extension dependencies (pycaw/comtypes COM interfaces, pyaudio, openwakeword ONNX runtime, pywebview CEF browser engine, piper TTS) that need careful PyInstaller spec configuration.

- [ ] Add `PyInstaller` to `requirements.txt` (dev dependency — not needed at runtime)
- [ ] Create `HADES.spec` — single-file or single-directory bundle (single-directory preferred for Windows antivirus compatibility); include `frontend/index.html`, `voices/` dir, `.env.example`, `openwakeword` model files
- [ ] Add hidden imports in spec: `pycaw`, `comtypes.gen`, `pyaudio`, `onnxruntime`, `openwakeword`, `sentence_transformers`, `spotipy`, `cv2`, `face_recognition` (optional), `pywebview` backends
- [ ] Add data files in spec: `frontend/index.html`, `voices/`, `openwakeword` default model files, `onnxruntime` shared libs
- [ ] Handle `comtypes` auto-generated COM interface files — these are written to a `comtypes/gen/` folder at runtime; configure `--runtime-tmpdir` or pre-generate them
- [ ] Exclude dev-only paths from bundle: `tests/`, `docs/`, `.git/`, `scripts/`, `*.md`
- [ ] Create `build.bat` — one-command build: `pyinstaller HADES.spec --clean`; outputs to `dist/HADES/`
- [ ] Piper binary inclusion: copy the Piper CLI binary and the voice model `.onnx` + `.onnx.json` into the bundle's `voices/` dir; update `_init_piper()` to find the binary relative to `sys._MEIPASS` when frozen
- [ ] Update `config.py` to detect `getattr(sys, 'frozen', False)` and resolve paths relative to `sys._MEIPASS` instead of `__file__`
- [ ] Test: bundled `.exe` launches, authenticates, speaks, listens, and executes at least one command from each handler category; no missing DLL errors on a clean machine without Python

**Done when**: `build.bat` produces a `dist/HADES/HADES.exe` (or single `.exe`) that runs on a Windows machine with no Python installed; all core features work; bundle size is documented.

---

## Phase 19: Action Log ⬜
**Goal**: Keep a reviewable record of every action HADES takes — commands executed, notes saved, reminders set, web searches opened, Spotify commands, power actions, etc. Lightweight audit trail required before shipping calendar write and email send in v1.5.

- [ ] Create `action_log.py` — `log_action(action_type, description, user_id=None, success=True)` function; writes to local `action_log.json` (rolling 500 entries, oldest pruned on write) and optionally to a Supabase `action_log` table
- [ ] Add `action_log` Supabase table to `scripts/supabase_schema.sql`: columns `id uuid`, `user_id uuid`, `timestamp timestamptz`, `action_type text`, `description text`, `success bool`; RLS: user can only read/write their own rows
- [ ] Wire `log_action()` into `router.py:route()` — after each handler returns a non-None result, log `(action_type=handler_class_name, description=response[:120])` without blocking the response path (fire-and-forget thread)
- [ ] Add `_ActionLogHandler` in `router.py` — intent: "what did you do", "show action log", "recent actions", "what have you done today"; returns the last 5–10 log entries formatted as a spoken list: "In the last hour I: opened Chrome, saved a note under work, played jazz on Spotify."
- [ ] Add `ACTION_LOG_ENABLED` env var to `config.py` and `.env.example` (default: `true`) — set to `false` to skip logging entirely (privacy mode)
- [ ] `action_log.json` added to `.gitignore`; `action_log` table added to Supabase schema doc
- [ ] Test: after a session of 5+ commands, "what did you do recently?" returns an accurate spoken list; log file never exceeds 500 entries; `ACTION_LOG_ENABLED=false` produces no writes

**Done when**: Action log is populated after every session; "recent actions" voice command works; log degrades gracefully (no crash) when Supabase is absent.

---

## Phase 20: Barge-in ⬜ (after Phase 17)
**Goal**: Allow the user to speak over HADES mid-sentence to interrupt and redirect it. Depends on Phase 17 (streaming TTS) because barge-in only makes sense when responses are spoken incrementally — interrupting a full-block speak() call would require killing it anyway, but streaming gives a natural seam.

**Strategy**: run a lightweight voice-activity detection (VAD) thread during TTS playback. When mic energy exceeds a threshold, set an interrupt `threading.Event`; the TTS playback loop checks this event between chunks and stops. The interrupted speech is then captured normally by `listen()`.

- [ ] Add `BARGE_IN_ENABLED` boolean env var to `config.py` and `.env.example` (default: `true`)
- [ ] Add `voice/vad.py` — `VoiceActivityDetector` class; opens a secondary `pyaudio` input stream at 16 kHz; in a background thread, computes RMS energy per 20 ms frame; if energy exceeds `VAD_THRESHOLD` (env var, default: `500`) for at least 2 consecutive frames, sets `self.triggered` event
- [ ] Modify `voice/tts.py:speak_streaming()` (Phase 17) — accepts an optional `interrupt_event: threading.Event`; checks the event between every audio chunk; if set, stops playback, closes the audio stream, and returns early with a `interrupted=True` flag
- [ ] Modify `main.py:hades_loop()` — create a `VAD` instance before TTS starts; pass its `triggered` event to `speak_streaming()`; if the speak returns early (interrupted), skip the follow-up window setup and immediately call `listen()` to capture the barge-in speech; route it normally
- [ ] Handle device conflict: both VAD (input) and TTS (output) use pyaudio — open them on separate streams (one input device, one output device); full-duplex is supported by most Windows audio drivers; fall back gracefully if the input stream fails to open during TTS
- [ ] Add debounce: ignore VAD triggers for 300 ms after TTS starts to avoid the TTS output itself triggering the VAD (acoustic echo)
- [ ] Test: saying "stop" or asking a new question while HADES is mid-sentence interrupts cleanly within 200 ms; the new question is routed correctly; non-barge-in responses complete normally; `BARGE_IN_ENABLED=false` disables the VAD thread entirely

**Done when**: Mid-sentence interruption stops TTS within 200 ms, captures the new input, and routes it; no audio device errors on a standard Windows machine; `BARGE_IN_ENABLED=false` restores original behavior.
