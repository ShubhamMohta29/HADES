# Document 03 — App Flow: Navigation & User Journey Map

## Pages / Views
HADES is a single-window desktop app with one screen. There is no navigation between pages.

| View | Description |
|---|---|
| Main window | The only screen — orb, chat log, text input bar |

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

---

## Entry Point
User launches `main.py`. The pywebview window opens immediately. The voice loop starts on a background thread. HADES speaks "Hades online. All systems nominal. Say my name to activate."

If `FACE_AUTH_ENABLED=true`: face verification runs first. Pass → normal boot. Fail → "Access denied" spoken and voice loop exits (GUI stays open but unresponsive to voice).

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
10. Loop returns to **LISTENING** (user can continue without re-saying "HADES")
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
6. Sent to Groq Llama 4 Scout with user's prompt
7. Response spoken + displayed in chat
8. Orb → STANDBY

---

## Orb States

| State | Visual | Trigger |
|---|---|---|
| standby | Slow pulse, default cyan glow | App idle at startup, waiting for wake word |
| sleeping | Near-dark orb (15% brightness), rings/ticks faded to 10% opacity, very slow pulse (9s) | User triggered sleep; mic active but only wake word is processed |
| listening | Fast pulse (1.2s), bright glow | Wake word detected, mic active for commands |
| thinking | Amber hue-shift, rapid pulse (0.8s) | Processing input (routing/LLM) |
| speaking | Blue-white tint, fastest pulse (0.6s) | Piper TTS playing |

State is set via `gui.set_status(state)` which calls JS `setStatus(state)` which updates `document.body.dataset.status` and the status text element.

---

## Sleep / Deactivation Flow
- Triggers (voice or text): "sleep", "goodbye", "good bye", "goodnight", "good night", "that's all", "stand by", "standby", "go to sleep"
- **Via voice loop**: HADES speaks "Going to sleep, Sir. Call me when you need me." → inner command loop breaks → outer loop sets `_sleeping = True` → orb enters **sleeping** state → `wait_for_wake_word()` keeps mic open but discards all speech except the wake word → user says "HADES" → HADES responds "I'm back, Sir. What do you need?" → `_sleeping` reset → command mode resumes
- **Via text input**: `handle_text_command()` detects sleep words → clears `_pending_state` → orb enters **sleeping** state → HADES speaks and logs "Shutting down, Sir. Goodnight." → returns early without resetting to STANDBY → `_text_state["sleeping"]` flag set; next text command wakes back to STANDBY before routing (voice loop is unaffected)

---

## Help Command Flow
- Trigger: "help", "commands", "what can you do", "show commands", "command list" (exact phrases only — "help me with X" falls through to screen/AI)
- `gui.add_help_card(HELP_HTML)` renders a styled card in the chat panel with all command categories
- HADES speaks: "Here is a list of things I can help you with, Sir." — does **not** read every command aloud
- Available anytime by voice or text input

---

## Note-Taking Flow (Conversational)
1. User says or types a note trigger: "take a note: finish the report"
2. Router extracts the note content, calls `_start_note_flow(content)`
3. LLM picks the best-fit category from the user's existing categories (defaults: `personal`, `work`)
4. HADES speaks: "Which category should I file this under? You have: 'personal', 'work'. I suggest 'work', Sir."
5. User replies with: a known category name / "yes" or "sure" (uses suggestion) / a new single word (creates new category)
6. Note saved with `[category]` tag; HADES confirms: "Note saved under 'work', Sir."
7. If the user says something ambiguous, HADES re-asks once
8. Saying a sleep word while awaiting a category abandons the note and enters sleep

---

## Memory Reset Flow
- User says or types "clear memory" / "forget everything"
- `brain.clear_memory()` called → `conversation_history.json` reset to system-prompt-only
- Response: "Memory cleared, Sir." spoken and shown in chat

---

## Empty States
- **No notes yet**: "Your notes are empty, Sir."
- **No notes in category**: "No notes found under 'work', Sir."
- **No mic available**: `listen()` returns `MIC_ERROR` sentinel (not `None`). After 3 consecutive `MIC_ERROR` returns the voice loop shows "Microphone unavailable — use the text input, Sir." in the GUI. When the mic comes back the loop shows "Microphone reconnected." Text input continues to work throughout.
- **No Piper model**: TTS logs error, falls back to print-only (no audio)
- **API key missing**: Each module checks at import time and returns a human-readable error string

## Error States

| Error | Response |
|---|---|
| Groq API error | "My connection to the language server is disrupted, Sir. Try again in a moment." |
| Google STT failure | `listen()` returns `None` → loop continues listening |
| Mic unavailable (OSError) | `listen()` returns `MIC_ERROR` sentinel → after 3 in a row, GUI shows text-only warning |
| Wake word timeout | `WaitTimeoutError` caught → continue polling |
| Wake word double-fire | Debounce (2.5 s default) silently ignores rapid re-trigger |
| Spotify 401 | "Spotify authentication has expired, Sir. Restart HADES to re-authenticate." |
| Spotify 403 / Premium | "That action requires Spotify Premium, Sir." |
| Spotify 429 | "Spotify's rate limit has been reached, Sir. Try again in a moment." |
| Spotify not connected | Spotipy OAuth triggers browser login on first use |
| Vision rate limit | "I've hit my vision rate limit, Sir. Try again in a moment." |
| App/path not found | "Could not find {app} at the expected path, Sir." |
| Face auth failed | "I don't recognize you, Sir. Access denied." → voice loop exits |

---

## Redirects / Navigation
There are no redirects — it's a single-window app. Spotify OAuth opens a browser window temporarily for initial auth, then closes.
