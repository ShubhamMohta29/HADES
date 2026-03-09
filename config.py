import os
from dotenv import load_dotenv

load_dotenv()

# ── Required ─────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── Free APIs (get keys at the links below) ───────────────────────────────────
# https://openweathermap.org/api  (free tier)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

# https://newsapi.org  (free tier - 100 requests/day)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# ── Spotify (optional) ────────────────────────────────────────────────────────
# https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI  = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Settings ──────────────────────────────────────────────────────────────────
DEFAULT_CITY     = os.getenv("DEFAULT_CITY", "Toronto")   # change to your city
FACE_AUTH_ENABLED = os.getenv("FACE_AUTH_ENABLED", "false").lower() == "true"