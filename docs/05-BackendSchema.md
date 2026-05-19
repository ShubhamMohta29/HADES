# Document 05 — Backend Schema: Data Model & Architecture

HADES has no relational database. All persistence is flat-file. This document covers the data structures, file formats, module responsibilities, and API contracts.

---

## Persistent Files

### `conversation_history.json`
Stores the full conversation as a JSON array of message objects.

```json
[
  { "role": "system",    "content": "<SYSTEM_PROMPT>" },
  { "role": "user",      "content": "What's the weather?" },
  { "role": "assistant", "content": "It's 18°C and sunny in Toronto, Sir." },
  ...
]
```

**Constraints**:
- First element is always `role: system`; content is refreshed from `SYSTEM_PROMPT` on every load
- Trimmed to `[system] + last 40 messages` (20 turns × 2) on every write
- Thread-safe: guarded by `threading.Lock()`
- Written to disk after every assistant reply via `save_memory()`
- Currently local, want to make it stored on something like supabase or such to free up that storage from the system.

---

### `notes.txt`
Append-only plain text file. One note per line.

```
[2025-05-17 14:32] refactor auth tomorrow
[2025-05-17 15:01] [personal] call dentist
[2025-05-17 16:00] [work] finish the API redesign doc
```

**Category tag** is optional. When present it appears as `[word]` immediately after the timestamp.

**Written by**: `commands.save_note(note, category=None)` — appends `[YYYY-MM-DD HH:MM] [category] {note}\n` (category omitted if `None`)
**Read by**: `commands.read_notes(category=None)` — returns all lines, or filters by category tag if given
**Categories listed by**: `commands.get_existing_categories()` — scans the file for `[letters-only]` tags, defaults to `["personal", "work"]` if none exist yet

> Supabase migration planned — see doc 07.

---

### `.env`
Secrets file, never committed. Loaded by `python-dotenv` at startup.

```
GROQ_API_KEY=...
WEATHER_API_KEY=...
NEWS_API_KEY=...
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
DEFAULT_CITY=Toronto
FACE_AUTH_ENABLED=false
PIPER_MODEL=
```

---

### `voices/en_GB-alan-medium.onnx` + `.onnx.json`
Binary Piper TTS voice model. Read once at first `speak()` call. Not committed to git (too large). Downloaded manually by the user.

---

### Spotify OAuth Cache
`spotipy` auto-creates a `.cache` file in the working directory after first OAuth login. Contains access/refresh tokens. Not committed.

---

## Module Responsibilities

| Module | Owns | Side effects |
|---|---|---|
| `brain.py` | `conversation_history` list, `conversation_history.json` | Writes JSON on every reply |
| `commands.py` | `notes.txt` (read + categorised write), volume, OS shell calls | Appends to notes; fires system commands; exposes `HELP_HTML` constant |
| `voice.py` | Mic stream, Piper audio output | Plays audio; prints to stdout |
| `vision.py` | Screen capture (ephemeral) | No persistence |
| `weather.py` | None | HTTP GET to OpenWeatherMap |
| `news.py` | None | HTTP GET to NewsAPI |
| `stocks.py` | None | HTTP GET to yfinance / CoinGecko |
| `spotify.py` | Spotify OAuth `.cache` | Controls Spotify client |
| `face_auth.py` | Face embedding (in-memory) | Accesses camera |
| `gui.py` | pywebview window | Calls JS via evaluate_js |
| `config.py` | `.env` values | None (read-only) |
| `main.py` | Voice loop, intent routing | Orchestrates all modules |

---

## Intent Routing Logic (`main.py:route()`)

Priority order (first match wins):

```
0. _pending_state active                   → _handle_pending_state(t)   ← multi-turn (e.g. note category)
1. "clear memory" / "forget everything"   → brain.clear_memory()
2. Screen keywords                         → vision.analyze_screen()
3. "help" / "commands" / exact phrases    → gui.add_help_card() + short spoken intro
4. Note-taking triggers                    → _start_note_flow(note)      ← conversational category selection
5. "weather"                               → weather.get_weather(city)
6. "news" / "headlines"                   → news.get_news(topic)
7. stock regex (\bstock\b|\bshare price\b) → stocks.get_stock(symbol)   ← handles "Tesla stock" AND "stock Tesla"
8. crypto coin keywords                    → stocks.get_crypto(coin_id)
9. Spotify trigger phrases                 → spotify.spotify_command(text)
10. PC commands (volume, time, apps, etc.) → commands.handle_command(text)
11. fallback                               → brain.think(text)
```

### Multi-turn note flow (`_pending_state`)

When note content is detected but no category specified:
1. `_start_note_flow(content)` — reads existing categories, calls LLM to pick best fit, stores `_pending_state`, asks user
2. Next `route()` call — `_handle_pending_state(t)` parses: known category name → saves; affirmative ("yes"/"sure") → uses suggestion; single new word → creates new category; ambiguous → re-asks once
3. Saying a sleep word clears `_pending_state` immediately

---

## Auth Architecture

### Groq API
- API key in `.env` → `GROQ_API_KEY`
- Passed to `groq.Groq(api_key=...)` at module load
- No user-facing auth; single key per instance

### Spotify OAuth (PKCE via spotipy)
- Client ID + secret in `.env`
- `SpotifyOAuth` flow; browser opens automatically on first use
- Token cached in `.cache` file; auto-refreshed on expiry
- Scopes: `user-read-playback-state user-modify-playback-state user-read-currently-playing`

### Google STT
- No API key — uses the `speech_recognition` library's free tier endpoint
- Internet connection required; requests are unauthenticated. Should authenticate them

### Face Auth (optional)
- No external service — `face_recognition` runs locally via dlib
- Reference embeddings loaded from `known_faces/` directory at startup
- Threshold: cosine distance < 0.6 = match (library default)

---

## External API Contracts

### OpenWeatherMap
```
GET https://api.openweathermap.org/data/2.5/weather
  ?q={city}&appid={key}&units=metric
Response: { main.temp, weather[0].description, name }
```

### NewsAPI
```
GET https://newsapi.org/v2/top-headlines
  ?country=us&q={topic}&apiKey={key}&pageSize=5
Response: { articles[].title }
```

### yfinance (stocks)
```python
ticker = yf.Ticker(symbol)
info = ticker.info  # dict with currentPrice, shortName
```

### CoinGecko (crypto)
```
GET https://api.coingecko.com/api/v3/simple/price
  ?ids={coin_id}&vs_currencies=usd
Response: { bitcoin: { usd: 65000 } }
```

### Groq Chat Completions
```python
client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[...],
    max_tokens=400,
    temperature=0.7,
)
```

### Groq Vision
```python
client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[
        {
            "role": "system",
            "content": (
                "You are HADES. A screenshot has been captured and attached — "
                "describe exactly what is visible in it. Never say you cannot "
                "see the screen; the image is present. Respond as HADES speaking "
                "directly. Address the user as Sir. Keep it to 2-3 sentences "
                "unless detail is required. No markdown or bullet points."
            )
        },
        { "role": "user", "content": [image_url, text] }
    ],
    max_tokens=500,
    temperature=0.5,
)
```

The system prompt is required to prevent the model from denying screen access or responding as a generic assistant. The user-facing `text` prompt (built in `main.py:route()`) is phrased imperatively: `"Describe what you see in the attached screenshot and help the user with their request: '...'"`.


---

## GUI ↔ Python Bridge

### Python → JS (via `gui.evaluate_js`)
| JS function | Called when |
|---|---|
| `addMessage(who, text)` | New chat message to display |
| `addSystemMessage(text)` | System event (boot, auth, mic status, etc.) |
| `setStatus(state)` | Orb state change |
| `addHelpCard(html)` | User says "help" or "commands" — renders the styled command reference card |

### JS → Python (via `pywebview.api`)
| Python method | JS call |
|---|---|
| `api.send_message(text)` | User clicks SEND or presses Enter |

---

## Security Considerations

- `.env` must never be committed; `.gitignore` excludes it
- Spotify `.cache` must never be committed; excluded from git
- `conversation_history.json` contains private conversations; treated as local-only
- No network server is exposed; pywebview uses a local webview, not a TCP port
- Shell commands (`os.system`, `subprocess.Popen`) are called with hardcoded paths or controlled inputs — not from raw user text passed to a shell
- Screen capture is triggered only by explicit user intent phrases
