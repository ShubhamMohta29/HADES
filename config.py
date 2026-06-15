"""Config / .env loader."""

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
NEWS_API_KEY    = os.getenv("NEWS_API_KEY", "")

# Spotify (optional) — https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI  = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

# Settings
DEFAULT_CITY      = os.getenv("DEFAULT_CITY", "Toronto")
FACE_AUTH_ENABLED = os.getenv("FACE_AUTH_ENABLED", "false").lower() == "true"

# Piper TTS voice model path — set this in .env if you place the .onnx elsewhere
PIPER_MODEL = os.getenv("PIPER_MODEL", "")  # empty = default ./voices/en_GB-alan-medium.onnx

# Supabase (optional — enables cloud memory + semantic search)
SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Wake word settings
# Comma-separated list of wake words (e.g. "hades,jarvis"). First is primary.
WAKE_WORDS_ENV    = os.getenv("WAKE_WORDS", "hades")
# Seconds to ignore a second wake-word trigger after the first (prevents echo double-fire)
WAKE_DEBOUNCE     = float(os.getenv("WAKE_DEBOUNCE", "2.5"))
# Neural wake word (Phase 14) — set to false to force STT-based fallback
NEURAL_WAKE_WORD  = os.getenv("NEURAL_WAKE_WORD", "true").lower() == "true"
# Path to a custom openwakeword .onnx model; empty = use all built-in default models
WAKE_MODEL        = os.getenv("WAKE_MODEL", "")

# Continuous conversation (Phase 15)
# Seconds of silence after a reply before returning to standby
FOLLOWUP_TIMEOUT  = float(os.getenv("FOLLOWUP_TIMEOUT", "15"))

# Action confirmation gate (Phase 16)
# Seconds before an unconfirmed destructive action is auto-cancelled
CONFIRM_TIMEOUT   = float(os.getenv("CONFIRM_TIMEOUT", "10"))
