# Document 03 — App Flow: Navigation & User Journey Map

## Pages / Views
HADES is a single-window desktop app with one screen. There is no navigation between pages.

| View | Description |
|---|---|
| Main window | The only screen — login panel (when needed), orb, chat log, text input bar |

---

## Layout (top to bottom)

```
┌─────────────────────────────────────────────┐
│  [ HUMAN ASSISTANCE AND DECISION ENGINEERING SYSTEM  v3.0 ]  ← titlebar
├─────────────────────────────────────────────┤
│                                             │
│         [animated orb + rings]              │ ← stage (320px)
│              H.A.D.E.S                      │
│           ◉  STANDBY                        │
│                                             │
├─────────────────────────────────────────────┤
│  — All systems nominal. Waiting...  —       │ ← chat log (scrollable)
│  12:04  HADES: Yes, Sir?                    │
│  12:04  You: what's the weather             │
│  12:04  HADES: It's 18°C and sunny...       │
├─────────────────────────────────────────────┤
│  [ Type a command...          ] [ SEND ]    │ ← input bar
└─────────────────────────────────────────────┘
```

Login panel (shown before above layout when Supabase is configured and no valid session):
```
┌─────────────────────────────────────────────┐
│              H.A.D.E.S                      │
│         IDENTIFY YOURSELF                   │
│                                             │
│  [ email@example.com            ]           │
│  [ password                     ]           │
│  [ AUTHENTICATE ]  [ MAGIC LINK ]           │
│                                             │
│         [ SKIP — LOCAL MODE ]               │
└─────────────────────────────────────────────┘
```

---

## Entry Point

User launches `main.py`. The pywebview window opens immediately.

**Auth flow** (before voice loop starts):
1. GUI loads → `_on_loaded()` fires
2. If Supabase is **not** configured (`SUPABASE_URL` absent): login panel is hidden; `on_auth_complete(None)` fires immediately → voice loop starts in local mode
3. If Supabase **is** configured:
   - Check `~/.jarvis/session.json` for a valid token → `db.restore_session(access_token, refresh_token)` → if valid, `on_auth_complete(user_id)` fires silently
   - If no token / token expired → login panel is shown; user submits credentials → JS calls `api.login(email, password)` or `api.magic_link(email)` or `api.skipLogin()` → `on_auth_complete(user_id or None)` fires
4. Voice loop thread (blocked on `_auth_event`) unblocks and calls `hades_loop(gui, user_id)`

If `FACE_AUTH_ENABLED=true`: face verification runs first inside `hades_loop()`. Pass → normal boot. Fail → "Access denied" spoken and voice loop exits (GUI stays open but HADES is inactive).

---

## Core User Journey 1 — Voice Command

1. App is in **STANDBY** state (orb pulses slowly, status reads "STANDBY")
2. User says "HADES"
3. Wake word detected → orb shifts to **LISTENING** state → HADES speaks "Yes, Sir?"
4. User speaks a command, e.g. "What's the weather in London?"
5. Mic captures audio → Google STT transcribes → message appears in chat as "You: ..."
6. Orb shifts to **THINKING** state
7. Router matches "weather" keyword → calls OpenWeatherMap → formats reply
8. Orb shifts to **SPEAKING** state → Piper TTS plays response
9. Reply appears in chat as "HADES: ..."
10. Loop enters **FOLLOW-UP** state — orb dims to `followup` CSS state; mic stays open for up to `FOLLOWUP_TIMEOUT` seconds of silence; user can ask follow-ups without re-saying "HADES"
11. User says "sleep" / "goodbye" / "goodnight" / "stand by" / "that's all" → HADES says "Going to sleep, Sir" → orb enters **SLEEPING** state → mic remains open but only the wake word is processed; all other speech is discarded → user says "HADES" → HADES responds "I'm back, Sir" → resumes command mode

---

## Core User Journey 2 — Text Command

1. App open in any state
2. User types in the input bar and presses Enter or clicks SEND
3. Message appears in chat as "You: ..."
4. `handle_text_command()` called on a new thread (does not block GUI)
5. If a sleep word is detected (e.g. "go to sleep", "goodbye"):
   - Orb enters **SLEEPING** state; HADES speaks and logs "Shutting down, Sir. Goodnight."
   - Function returns early — orb stays in SLEEPING, not reset to STANDBY
   - Next text command automatically wakes HADES back to STANDBY before routing
6. Otherwise: orb transitions through THINKING → SPEAKING states
7. Piper TTS speaks the reply; reply appears in chat
8. Orb returns to STANDBY

---

## Core User Journey 3 — Screen Analysis

1. User (by voice or text) says "What's on my screen?" / "Help me with my homework"
2. Router matches screen analysis keywords
3. Orb → THINKING; `vision.analyze_screen()` called
4. `PIL.ImageGrab.grab()` captures full screen
5. Image resized to 1280px wide, converted to base64 JPEG
6. Sent to Groq Llama 4 Scout with HADES persona system prompt + user's prompt
7. Response spoken + displayed in chat
8. Orb → STANDBY

---

## Core User Journey 4 — Authentication

1. App launches; Supabase is configured; no valid session file found
2. Login panel shown (email + password fields; magic link button; skip button)
3a. User enters email + password → clicks AUTHENTICATE → JS calls `api.login(email, password)`
    → `db.sign_in()` → session saved to `~/.jarvis/session.json` → login panel hidden
    → `on_auth_complete(user_id)` fires → voice loop starts
3b. User clicks MAGIC LINK → JS calls `api.magic_link(email)` → Supabase sends OTP email
    → GUI shows "Check your email, Sir" message (manual token entry not yet implemented)
3c. User clicks SKIP — LOCAL MODE → JS calls `api.skipLogin()` → login panel hidden
    → `on_auth_complete(None)` fires → voice loop starts in local mode (flat-file storage)
4. On subsequent launches: `~/.jarvis/session.json` token is valid → auth is silent (no panel shown)

---

## Orb States

| State | Visual | Trigger |
|---|---|---|
| standby | Slow pulse (3.2s), default cyan glow | App idle, waiting for wake word |
| sleeping | Near-dark (15% brightness), rings/ticks at 10% opacity, very slow pulse (9s) | User triggered sleep; mic active but only wake word processed |
| listening | Fast pulse (1.2s), bright oversized glow | Wake word detected; mic active for commands |
| followup | Dim cyan (65% brightness, +20° hue), slower pulse (2s), muted status color | After HADES speaks; follow-up window open; mic active for up to FOLLOWUP_TIMEOUT seconds |
| thinking | `hue-rotate(40deg)` amber shift, rapid pulse (0.8s) | Processing input (routing/LLM) |
| speaking | `hue-rotate(-30deg) saturate(1.4)` blue-white shift, fastest pulse (0.6s) | Piper TTS playing |

State is set via `gui.set_status(state)` → JS `setStatus(state)` → `document.body.dataset.status`.

---

## Sleep / Deactivation Flow

Triggers (voice or text): "sleep", "goodbye", "good bye", "goodnight", "good night", "that's all", "stand by", "standby", "go to sleep"

- **Via voice loop**: HADES speaks "Going to sleep, Sir. Call me when you need me." → inner command loop breaks → outer loop sets `_sleeping = True` → orb enters **sleeping** state → `wait_for_wake_word()` keeps mic open but discards all speech except the wake word → user says "HADES" → HADES responds "I'm back, Sir. What do you need?" → `_sleeping` reset → command mode resumes
- **Via text input**: `handle_text_command()` detects sleep words → clears `_pending_state` → orb enters **sleeping** state → HADES speaks and logs "Shutting down, Sir. Goodnight." → returns early without resetting to STANDBY → `_text_state["sleeping"]` flag set; next text command wakes back to STANDBY before routing (voice loop is unaffected)

---

## Help Command Flow

- Trigger: "help", "commands", "what can you do", "show commands", "command list", "what can i say" (exact phrases only — "help me with X" falls through to screen/AI)
- `gui.add_help_card(HELP_HTML)` renders a styled card in the chat panel with all command categories
- HADES speaks: "Here is a list of things I can help you with, Sir." — does **not** read every command aloud
- Available anytime by voice or text input

---

## Note-Taking Flow (Conversational)

1. User says or types a note trigger: "take a note: finish the report"
2. Router extracts the note content; calls `_start_note_flow(content, user_id)`
3. LLM picks the best-fit category from the user's existing categories (defaults: `personal`, `work`)
4. HADES speaks: "Which category should I file this under? You have: 'personal', 'work'. I suggest 'work', Sir."
5. User replies with: a known category name / "yes" or "sure" (uses suggestion) / a new single word (creates new category)
6. Note saved via `commands.save_note()` (Supabase if available, else notes.txt); HADES confirms: "Note saved under 'work', Sir."
7. If the user says something ambiguous, HADES re-asks once
8. Saying a sleep word while awaiting a category abandons the note and enters sleep

---

## Note Deletion Flow

- **Delete last note**: "delete my last note" → executes immediately → `commands.delete_last_note(user_id)` → confirms "Done, Sir. Your last note has been deleted."
- **Delete category**: "delete my work notes" → enters **confirm gate** → HADES: "Are you sure you want to delete all your work notes, Sir?" → user says "yes" → `commands.delete_notes("work", user_id)` → confirms; "no" → "Cancelled, Sir."
- **Delete all**: "delete all my notes" → enters **confirm gate** → HADES: "Are you sure you want to delete all your notes, Sir? This cannot be undone." → user says "yes" → `commands.delete_notes(user_id=user_id)` → confirms; "no" → "Cancelled, Sir."

---

## Action Confirmation Gate Flow (Phase 16)

Triggered by: `shutdown`, `restart`, `delete all notes`, `delete [category] notes`.

1. Router matches a destructive command
2. Instead of executing, `_PowerConfirmHandler` or `_DeleteNoteHandler` stores the deferred callable in `_pending_state["action"] = "confirm_action"` with a `set_at` timestamp
3. HADES speaks the confirmation prompt: "Are you sure you want to {description}, Sir?"
4. On the **next** voice or text input, `_handle_confirm_state()` is called:
   - **Confirm words** (`yes`, `confirm`, `go ahead`, `proceed`, `sure`, …) → execute the stored callable → speak result
   - **Deny words** (`no`, `cancel`, `stop`, `abort`, `never mind`, …) → clear state → "Cancelled, Sir."
   - **Timeout**: if `time.time() - set_at > CONFIRM_TIMEOUT` (default 10s) → auto-cancel → "Confirmation timed out. Action cancelled, Sir."
   - **Ambiguous**: re-prompt once — "Please confirm — {description}? Say 'yes' to proceed or 'no' to cancel, Sir."
5. Sleep words during confirmation window clear `_pending_state` and enter sleep normally

Commands that bypass the gate: `cancel shutdown`, `lock` (both non-destructive, execute immediately).

---

## Memory Reset Flow

- User says or types "clear memory" / "forget everything"
- `brain.clear_memory(user_id)` called → clears Supabase `conversation_memory` rows (if Supabase active) **and** resets `conversation_history.json` to system-prompt-only
- Response: "Memory cleared, Sir." spoken and shown in chat

---

## Empty States

- **No notes yet**: "Your notes are empty, Sir."
- **No notes in category**: "No notes found under 'work', Sir."
- **No mic available**: `listen()` returns `MIC_ERROR` sentinel. After 3 consecutive `MIC_ERROR` returns the voice loop shows "Microphone unavailable — use the text input, Sir." in the GUI. When the mic comes back the loop shows "Microphone reconnected."
- **No Piper model**: TTS logs error, auto-downloads the default model; if download fails, falls back to print-only
- **API key missing**: Each module checks and returns a human-readable error string
- **Supabase not configured**: Notes and memory silently fall back to flat-file storage

---

## Error States

| Error | Response |
|---|---|
| Groq API error | "My connection to the language server is disrupted, Sir. Try again in a moment." |
| Google STT failure | `listen()` returns `None` → loop continues listening |
| Mic unavailable (OSError) | `listen()` returns `MIC_ERROR` → after 3 in a row, GUI shows text-only warning |
| Wake word timeout | `WaitTimeoutError` caught → continue polling (STT path) or chunk loop continues (neural path) |
| Wake word double-fire | Debounce (2.5 s default) silently ignores rapid re-trigger on both neural and STT paths |
| Neural wake word error | Exception in `openwakeword` path → logged → falls back to `_stt_wait_for_wake_word()` for that call |
| Confirm timeout | No voice input within `CONFIRM_TIMEOUT` seconds → auto-cancel on next interaction |
| Supabase auth error | Spoken error; falls back to local mode |
| Supabase DB error | Logged; notes/memory fall back to flat-file silently |
| Spotify 401 | "Spotify authentication has expired, Sir. Restart HADES to re-authenticate." |
| Spotify 403 / Premium | "That action requires Spotify Premium, Sir." |
| Spotify 429 | "Spotify's rate limit has been reached, Sir. Try again in a moment." |
| Spotify not connected | Spotipy OAuth triggers browser login on first use |
| Vision rate limit | "I've hit my vision rate limit, Sir. Try again in a moment." |
| App/path not found | "Could not find {app} at the expected path, Sir." |
| Face auth failed | "I don't recognize you, Sir. Access denied." → voice loop exits |

---

## Redirects / Navigation

There are no redirects — it's a single-window app. Spotify OAuth opens a browser window temporarily for initial auth, then closes. The login panel is rendered inside the same pywebview window and hidden (not destroyed) after auth completes.
