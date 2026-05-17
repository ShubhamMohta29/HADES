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

- [x] Volume: set to %, volume up/down/mute (pycaw + pyautogui fallback)
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

## Phase 11: Polish & Hardening (Remaining)
**Goal**: Reliability, error coverage, and user experience refinements.

- [ ] README with full setup instructions (API keys, Piper model download, venv setup)
- [ ] Graceful handling when mic is unavailable at startup (print warning, continue in text-only mode)
- [ ] Configurable wake words via `.env` (e.g. `WAKE_WORDS=hades,jarvis`)
- [ ] Debounce rapid double-wake-word triggers
- [ ] Trim Spotify error messages to be voice-friendly
- [ ] Add "help" command that lists available commands spoken aloud
- [ ] Persist notes with optional category tagging
- [ ] Test suite for `route()` logic (unit tests, no voice/API calls needed)

---

## Phase 12: Distribution (Future)
**Goal**: Make it easy for others to install and run.

- [ ] `setup.py` or `pyproject.toml` for pip-installable packaging
- [ ] GitHub Releases with bundled Windows `.exe` (PyInstaller)
- [ ] Auto-download Piper voice model on first run if not present
- [ ] One-command install script (`install.bat`)

---

## Done Criteria (v1 Shipped)

- [ ] All Phase 1–10 items checked off
- [ ] App starts cold in under 10 seconds
- [ ] Wake word triggers reliably in a quiet room
- [ ] All 8 command categories tested: AI chat, weather, news, stocks, crypto, Spotify, PC control, screen vision
- [ ] No unhandled exceptions in a 30-minute voice session
- [ ] `.env.example` documents every required key
- [ ] `README.md` covers install, setup, and first-run steps
