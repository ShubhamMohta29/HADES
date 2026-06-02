"""Smoke test — verify all configured API keys are valid before first run.

Run with:  python smoke_test.py
Each check prints PASS / FAIL / SKIP (if the key is not set).
Exit code is 0 if all configured keys pass, 1 if any fail.
"""

import sys
import os

# Load .env before importing config
from dotenv import load_dotenv
load_dotenv()

PASS  = "\033[92mPASS\033[0m"
FAIL  = "\033[91mFAIL\033[0m"
SKIP  = "\033[93mSKIP\033[0m"

results = []


def check(name: str, key_var: str, fn):
    key = os.getenv(key_var, "")
    if not key:
        print(f"  {SKIP}  {name} ({key_var} not set)")
        return
    try:
        fn(key)
        print(f"  {PASS}  {name}")
        results.append(True)
    except Exception as e:
        print(f"  {FAIL}  {name}: {e}")
        results.append(False)


print("\nHADES — API Key Smoke Test")
print("=" * 40)

# ── Groq ────────────────────────────────────────────────────────────────────
def _check_groq(key):
    from groq import Groq
    r = Groq(api_key=key).chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1,
    )
    assert r.choices

check("Groq (LLM)", "GROQ_API_KEY", _check_groq)

# ── OpenWeatherMap ───────────────────────────────────────────────────────────
def _check_weather(key):
    import requests
    r = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": "London", "appid": key},
        timeout=8,
    )
    if r.status_code == 401:
        raise ValueError("Invalid API key")
    r.raise_for_status()

check("OpenWeatherMap (weather)", "WEATHER_API_KEY", _check_weather)

# ── NewsAPI ──────────────────────────────────────────────────────────────────
def _check_news(key):
    import requests
    r = requests.get(
        "https://newsapi.org/v2/top-headlines",
        params={"country": "us", "pageSize": 1, "apiKey": key},
        timeout=8,
    )
    data = r.json()
    if data.get("status") != "ok":
        raise ValueError(data.get("message", "Unknown error"))

check("NewsAPI (news)", "NEWS_API_KEY", _check_news)

# ── Spotify ──────────────────────────────────────────────────────────────────
def _check_spotify(_key):
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    client_id     = os.getenv("SPOTIFY_CLIENT_ID", "")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not set")
    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
    )
    sp.search("test", limit=1)

# Spotify uses two keys; pass a dummy to the checker and let it read them internally
if os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"):
    check("Spotify", "SPOTIFY_CLIENT_ID", _check_spotify)
else:
    print(f"  {SKIP}  Spotify (SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET not set)")

# ── Supabase ─────────────────────────────────────────────────────────────────
def _check_supabase(key):
    supabase_url = os.getenv("SUPABASE_URL", "")
    if not supabase_url:
        raise ValueError("SUPABASE_URL not set")
    from supabase import create_client
    sb = create_client(supabase_url, key)
    # A simple anonymous ping — just fetching zero rows from a non-existent
    # table would raise; instead check the auth endpoint works.
    sb.auth.get_session()

check("Supabase", "SUPABASE_ANON_KEY", _check_supabase)

# ── Summary ──────────────────────────────────────────────────────────────────
print("=" * 40)
if not results:
    print("No keys configured to test. Add API keys to your .env file.")
    sys.exit(0)

failures = results.count(False)
if failures:
    print(f"{failures} check(s) FAILED. Fix the issues above before starting HADES.")
    sys.exit(1)
else:
    print("All configured keys are valid. HADES is ready to start.")
    sys.exit(0)
