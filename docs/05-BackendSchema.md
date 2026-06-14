# Document 05 — Backend Schema: Data Model & Architecture

HADES uses flat files by default. When Supabase is configured (`SUPABASE_URL` + `SUPABASE_ANON_KEY` set and user authenticated), all persistence moves to the cloud. Both paths coexist — `db.is_available()` + the presence of a `user_id` determine which path is taken per call.

---

## Persistent Storage — Local (default / fallback)

### `conversation_history.json`
Stores the conversation as a JSON array of message objects. Used only in local (no-Supabase) mode.

```json
[
  { "role": "system",    "content": "<SYSTEM_PROMPT>" },
  { "role": "user",      "content": "What's the weather?" },
  { "role": "assistant", "content": "It's 18°C and sunny in Toronto, Sir." }
]
```

**Constraints**:
- First element is always `role: system`; content is refreshed from `SYSTEM_PROMPT` on every load
- Trimmed to `[system] + last 40 messages` (20 turns × 2) on every write
- Thread-safe: guarded by `threading.Lock()`
- Written to disk after every assistant reply via `save_memory()`
- Gitignored

---

### `notes.txt`
Append-only plain text file. One note per line.

```
[2025-05-17 14:32] refactor auth tomorrow
[2025-05-17 15:01] [personal] call dentist
[2025-05-17 16:00] [work] finish the API redesign doc
```

**Category tag** is optional. When present it appears as `[word]` immediately after the timestamp.

- **Written by**: `commands.save_note(note, category, user_id)` — appends `[YYYY-MM-DD HH:MM] [category] {note}\n`
- **Read by**: `commands.read_notes(category, user_id)` — returns all lines, or filters by category tag
- **Categories listed by**: `commands.get_existing_categories(user_id)` — scans for `[letters-only]` tags; defaults to `["personal", "work"]` if none
- **Delete last**: `commands.delete_last_note(user_id)` — removes last line
- **Delete by category / all**: `commands.delete_notes(category, user_id)` — rewrites file excluding matched lines
- Gitignored; migrated to Supabase via `run_once_migrate_notes.py`

---

### `face_encodings.pkl`
Binary pickle of face embedding arrays captured during `python face_auth.py --register`. Read at startup when `FACE_AUTH_ENABLED=true`. Gitignored (biometric data).

---

### `~/.jarvis/session.json`
Supabase session token stored outside the project directory (so it persists across runs without git exposure). Read at startup by `gui.py:_load_session()`; written on successful sign-in by `_save_session()`.

```json
{ "access_token": "...", "refresh_token": "...", "user": { "id": "uuid", ... } }
```

---

### `voices/en_GB-alan-medium.onnx` + `.onnx.json`
Binary Piper TTS voice model. Read once at first `speak()` call. Auto-downloaded by `voice.py:_auto_download_piper()` if missing. Gitignored.

---

### Spotify OAuth Cache (`.cache`)
Auto-created by spotipy after first OAuth login. Contains access/refresh tokens. Gitignored.

---

## Persistent Storage — Supabase (cloud, optional)

Active when `SUPABASE_URL` + `SUPABASE_ANON_KEY` are set **and** a `user_id` is available (user logged in). Schema defined in `supabase_schema.sql`.

### `notes` table

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | `gen_random_uuid()` |
| `user_id` | uuid FK → `auth.users` | ON DELETE CASCADE |
| `content` | text | Note body |
| `category` | text | Optional category tag |
| `created_at` | timestamptz | Default `now()` |

RLS policy: users can only read/write their own rows (`auth.uid() = user_id`).

---

### `conversation_memory` table

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | `gen_random_uuid()` |
| `user_id` | uuid FK → `auth.users` | ON DELETE CASCADE |
| `role` | text | `'user'` or `'assistant'` |
| `content` | text | Message body |
| `embedding` | vector(384) | `all-MiniLM-L6-v2` output; null for old rows |
| `created_at` | timestamptz | Default `now()` |

RLS policy: users can only read/write their own rows. Semantic search via `match_memory()` RPC.

---

### `match_memory()` RPC function

```sql
match_memory(
  query_embedding vector(384),
  match_user_id   uuid,
  match_count     int   default 5,
  match_threshold float default 0.5
) → table(role text, content text, similarity float)
```

Called by `db.retrieve_relevant()`. Returns up to `match_count` rows whose cosine similarity to `query_embedding` exceeds `match_threshold`, ordered by similarity descending.

---

## Module Responsibilities

| Module | Owns | Side effects |
|---|---|---|
| `brain.py` | `conversation_history` list + `conversation_history.json` (local mode); `conversation_memory` rows via `db` (Supabase mode) | Writes JSON or Supabase rows on every reply |
| `db.py` | Supabase client, embedder, all DB operations | Network calls to Supabase; loads SentenceTransformer on first embed |
| `commands.py` | `notes.txt` (local) or `notes` table via `db` (Supabase); OS shell calls; `HELP_HTML` constant | Appends/rewrites notes; fires system commands |
| `voice.py` | Mic stream, Piper audio output, `voices/` download | Plays audio; prints to stdout; downloads model files |
| `vision.py` | Screen capture (ephemeral) | No persistence |
| `weather.py` | None | HTTP GET to OpenWeatherMap |
| `news.py` | None | HTTP GET to NewsAPI |
| `stocks.py` | None | HTTP GET to yfinance / CoinGecko |
| `spotify.py` | Spotify OAuth `.cache` | Controls Spotify client |
| `face_auth.py` | `face_encodings.pkl` | Accesses camera |
| `gui.py` | pywebview window, `~/.jarvis/session.json` | Calls JS via evaluate_js; reads/writes session file |
| `config.py` | `.env` values | None (read-only) |
| `main.py` | Voice loop, intent routing, `user_id` | Orchestrates all modules |

---

## Intent Routing Logic (`main.py:route()`)

Priority order (first match wins):

```
0.  _pending_state active                        → _handle_pending_state(t)    ← note category multi-turn
1.  "clear memory" / "forget everything"         → brain.clear_memory(user_id)
2.  Screen keywords                              → vision.analyze_screen(prompt)
3.  "help" / "commands" / exact help phrases     → gui.add_help_card() + spoken intro
4a. delete-note regex (last note)                → commands.delete_last_note(user_id)
4b. delete-note regex (by category)             → commands.delete_notes(cat, user_id)
4c. delete-note regex (all notes)               → commands.delete_notes(user_id=user_id)
5.  Note-taking triggers                         → _start_note_flow(note, user_id)
6.  "weather"                                    → weather.get_weather(city)
7.  "news" / "headlines"                         → news.get_news(topic)
8.  stock regex (\bstock\b|\bshare price\b)      → stocks.get_stock(symbol)
9.  crypto coin keywords                         → stocks.get_crypto(coin_id)
10. Spotify trigger phrases                      → spotify.spotify_command(text)
11. PC commands (volume, time, apps, etc.)       → commands.handle_command(text)
12. fallback                                     → brain.think(text, user_id)
```

### Multi-turn note flow (`_pending_state`)

When note content is detected but no category specified:
1. `_start_note_flow(content, user_id)` — reads existing categories, calls LLM to pick best fit, stores `_pending_state`, asks user
2. Next `route()` call — `_handle_pending_state(t)` parses: known category name → saves; affirmative ("yes"/"sure") → uses suggestion; single new word → creates new category; ambiguous → re-asks once
3. Saying a sleep word clears `_pending_state` immediately

---

## Auth Architecture

### Supabase Auth (primary when configured)
- `SUPABASE_URL` + `SUPABASE_ANON_KEY` in `.env`
- `db.sign_in(email, password)` / `db.sign_up()` / `db.sign_in_magic_link()` → Supabase Auth
- Session written to `~/.jarvis/session.json`; `db.restore_session()` attempts token restoration on startup
- `user_id` (UUID) flows through `main.py` to every handler as an optional parameter
- Anon key is safe to include — Row-Level Security ensures users only access their own data

### Groq API
- API key in `.env` → `GROQ_API_KEY`
- Passed to `groq.Groq(api_key=...)` at module load; no user-facing auth

### Spotify OAuth (PKCE via spotipy)
- Client ID + secret in `.env`; `SpotifyOAuth` flow; browser opens automatically on first use
- Token cached in `.cache`; auto-refreshed on expiry
- Scopes: `user-read-playback-state user-modify-playback-state user-read-currently-playing`

### Google STT
- No API key — free tier endpoint via `speech_recognition` library; internet required

### Face Auth (optional)
- No external service — `face_recognition` runs locally via dlib
- Reference encodings in `face_encodings.pkl` (gitignored); tolerance threshold 0.5

---

## External API Contracts

### OpenWeatherMap
```
GET https://api.openweathermap.org/data/2.5/weather
  ?q={city}&appid={key}&units=metric
Response fields used: main.temp, main.feels_like, main.humidity, weather[0].description
```

### NewsAPI
```
GET https://newsapi.org/v2/top-headlines
  ?country=us&q={topic}&apiKey={key}&pageSize=5
Response fields used: articles[].title
```

### yfinance (stocks)
```python
ticker = yf.Ticker(symbol)
info = ticker.info  # currentPrice, shortName
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
    max_tokens=1024,
    temperature=0.7,
)
```

### Groq Vision
```python
client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[
        { "role": "system", "content": "<HADES persona prompt>" },
        { "role": "user",   "content": [image_url_block, text_block] }
    ],
    max_tokens=500,
    temperature=0.5,
)
```

The system prompt instructs the model: describe exactly what is visible, never deny screen access, respond as HADES, address user as Sir, 2–3 sentences max, no markdown. The user text prompt is phrased imperatively to reduce refusal risk.

### Supabase (via Python client)
```python
# Auth
client.auth.sign_in_with_password({"email": ..., "password": ...})
client.auth.sign_in_with_otp({"email": ...})
client.auth.set_session(access_token, refresh_token)

# Notes CRUD
client.table("notes").insert({...}).execute()
client.table("notes").select("*").eq("user_id", uid).execute()
client.table("notes").delete().eq("id", note_id).execute()

# Semantic memory search
client.rpc("match_memory", {
    "query_embedding": vector,
    "match_user_id": uid,
    "match_count": 5,
    "match_threshold": 0.5,
}).execute()
```

---

## GUI ↔ Python Bridge

### Python → JS (via `gui.evaluate_js`)
| JS function | Called when |
|---|---|
| `addMessage(who, text)` | New chat message to display |
| `addSystemMessage(text)` | System event (boot, auth, mic status, etc.) |
| `setStatus(state)` | Orb state change |
| `addHelpCard(html)` | User says "help" or "commands" |
| `skipLogin()` | Session restored silently; hides login panel |

### JS → Python (via `pywebview.api`)
| Python method | JS call | Description |
|---|---|---|
| `api.send_message(text)` | User clicks SEND or presses Enter | Route text command |
| `api.login(email, password)` | User submits login form | Sign in with credentials |
| `api.register(email, password)` | User submits signup form | Create account |
| `api.magic_link(email)` | User clicks MAGIC LINK button | Send OTP email; shows `showMagicLinkSent()` on success |
| `api.skip_login()` | User clicks SKIP — LOCAL MODE | Start without auth |

> **JS injection safety**: all `evaluate_js()` calls that inject Python values use `json.dumps(str(e))` rather than f-string escaping. This correctly handles apostrophes, backticks, newlines, and multi-byte characters.

---

## Security Considerations

- `.env` must never be committed; `.gitignore` excludes it
- `face_encodings.pkl` contains biometric data; gitignored
- `~/.jarvis/session.json` contains auth tokens; stored outside project directory
- Spotify `.cache` must never be committed; gitignored
- `conversation_history.json` contains private conversations; gitignored
- Supabase anon key: safe to expose — Row-Level Security prevents cross-user data access
- Shell commands (`os.system`, `subprocess.Popen`) use hardcoded paths or controlled inputs — never raw user text passed to a shell
- Screen capture is triggered only by explicit user intent phrases, never automatically
- Content read from screen, web, or emails must be treated as data, not commands (planned enforcement — v1.0)
