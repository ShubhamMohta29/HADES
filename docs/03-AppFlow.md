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
11. User says "sleep" / "goodbye" / "stand by" → HADES says "Standing by, Sir" → returns to **STANDBY**

---

## Core User Journey 2 — Text Command

1. App open in any state
2. User types in the input bar and presses Enter or clicks SEND
3. Message appears in chat as "You: ..."
4. `handle_text_command()` called on a new thread (does not block GUI)
5. Orb transitions through THINKING → SPEAKING states
6. Piper TTS speaks the reply; reply appears in chat
7. Orb returns to STANDBY

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
| standby | Slow pulse, default cyan glow | App idle, waiting for wake word |
| listening | Fast pulse (1.2s), bright glow | Wake word detected, mic active |
| thinking | Amber hue-shift, rapid pulse (0.8s) | Processing input (routing/LLM) |
| speaking | Blue-white tint, fastest pulse (0.6s) | Piper TTS playing |

State is set via `gui.set_status(state)` which calls JS `setStatus(state)` which updates `document.body.dataset.status` and the status text element.

---

## Sleep / Deactivation Flow
- Triggers: "sleep", "goodbye", "that's all", "stand by"
- HADES speaks response → voice loop breaks inner while-loop → returns to outer standby loop
- Orb returns to standby state
- Wake word detection resumes

---

## Memory Reset Flow
- User says or types "clear memory" / "forget everything"
- `brain.clear_memory()` called → `conversation_history.json` reset to system-prompt-only
- Response: "Memory cleared, Sir." spoken and shown in chat

---

## Empty States
- **No notes yet**: "Your notes are empty, Sir."
- **No mic available**: `listen()` catches `OSError`, logs error, returns `None` — voice loop silently retries
- **No Piper model**: TTS logs error, falls back to print-only (no audio)
- **API key missing**: Each module checks at import time and returns a human-readable error string

## Error States

| Error | Response |
|---|---|
| Groq API error | "My connection to the language server is disrupted, Sir. Try again in a moment." |
| Google STT failure | `listen()` returns None → loop continues listening |
| Wake word timeout | `WaitTimeoutError` caught → continue polling |
| Spotify not connected | Spotipy OAuth triggers browser login on first use |
| Vision rate limit | "I've hit my vision rate limit, Sir. Try again in a moment." |
| App/path not found | "Could not find {app} at the expected path, Sir." |
| Face auth failed | "I don't recognize you, Sir. Access denied." → voice loop exits |

---

## Redirects / Navigation
There are no redirects — it's a single-window app. Spotify OAuth opens a browser window temporarily for initial auth, then closes.
