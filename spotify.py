"""Spotify control via spotipy — playback, search, and error handling.
Setup:
  1. pip install spotipy
  2. Go to https://developer.spotify.com/dashboard → create app
  3. Set redirect URI to http://localhost:8888/callback
  4. Add SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI to .env
"""
import logging
log = logging.getLogger("hades.spotify")

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-modify-playback-state user-read-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative user-library-read",
    open_browser=True  # auto-opens browser for auth
    ))
    SPOTIFY_AVAILABLE = True
except Exception:
    SPOTIFY_AVAILABLE = False

def get_active_device():
    devices = sp.devices()
    device_list = devices.get("devices", [])
    if not device_list:
        return None
    # Prefer active device, otherwise take first available
    for d in device_list:
        if d["is_active"]:
            return d["id"]
    return device_list[0]["id"]  # use first available if none active

def get_liked_songs_uri():
    """Get the context URI for user's liked songs."""
    return "spotify:user:" + sp.current_user()["id"] + ":collection"

def get_liked_songs_context():
    """Return a context object for liked songs (used for playback)."""
    return "spotify:collection"

def get_playlist_uri(playlist_name):
    """Search for a playlist by name and return its URI."""
    results = sp.current_user_playlists(limit=50)
    
    for playlist in results["items"]:
        if playlist_name.lower() in playlist["name"].lower():
            return playlist["uri"], playlist["name"]
    
    # If not found in first 50, try more
    while results.get("next"):
        results = sp.next(results)
        for playlist in results["items"]:
            if playlist_name.lower() in playlist["name"].lower():
                return playlist["uri"], playlist["name"]
    
    return None, None

def spotify_command(text):
    if not SPOTIFY_AVAILABLE:
        return "Spotify is not configured, Sir."

    t = text.lower()
    try:
        device_id = get_active_device()
        if not device_id:
            return "No Spotify device found. Please open Spotify and play something manually first, Sir."

        # ── Liked Songs ──────────────────────────────────────────────────────
        if "liked songs" in t or "saved songs" in t or "my favorites" in t:
            sp.start_playback(device_id=device_id, context_uri="spotify:collection")
            return "Playing your liked songs, Sir."

        # ── Playlist ─────────────────────────────────────────────────────────
        if "play" in t and "playlist" in t:
            # Extract playlist name: "play [playlist name] playlist"
            playlist_name = t.replace("play", "").replace("playlist", "").strip()
            if playlist_name:
                uri, name = get_playlist_uri(playlist_name)
                if uri:
                    sp.start_playback(device_id=device_id, context_uri=uri)
                    return f"Playing {name}, Sir."
                return f"Could not find playlist {playlist_name}, Sir."
            return "Which playlist, Sir?"

        # ── Specific Song ────────────────────────────────────────────────────
        if "play" in t and "spotify" not in t:
            query = t.replace("play", "").replace("music", "").replace("a song", "").replace("me", "").strip()
            
            if query:
                results = sp.search(q=query, limit=1, type="track")
                tracks = results["tracks"]["items"]
                if tracks:
                    sp.start_playback(device_id=device_id, uris=[tracks[0]["uri"]])
                    return f"Playing {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}, Sir."
                return f"Could not find {query} on Spotify, Sir."
            else:
                # No specific song — just resume
                sp.start_playback(device_id=device_id)
                return "Resuming playback, Sir."

        if "pause" in t or "stop music" in t:
            sp.pause_playback()
            return "Music paused, Sir."

        if "next" in t or "skip" in t:
            sp.next_track()
            return "Skipping, Sir."

        if "previous" in t or "last song" in t:
            sp.previous_track()
            return "Going back, Sir."

        if "what's playing" in t or "current song" in t:
            current = sp.current_playback()
            if current and current["is_playing"]:
                track = current["item"]
                return f"Currently playing {track['name']} by {track['artists'][0]['name']}, Sir."
            return "Nothing is currently playing, Sir."

        if "shuffle" in t:
            sp.shuffle(True)
            return "Shuffle enabled, Sir."

    except spotipy.exceptions.SpotifyException as e:
        return _spotify_error_summary(e)

    return None


def _spotify_error_summary(e) -> str:
    status = getattr(e, "http_status", None)
    detail = str(getattr(e, "reason", "") or str(e)).lower()
    log.error("Spotify API error (HTTP %s): %s", status, e)

    if status == 401:
        return "Spotify authentication has expired, Sir. Restart HADES to re-authenticate."
    if status == 403 or "premium" in detail:
        return "That action requires Spotify Premium, Sir."
    if status == 404 or "not found" in detail:
        return "Spotify couldn't find that resource, Sir. It may have been removed."
    if status == 429:
        return "Spotify's rate limit has been reached, Sir. Try again in a moment."
    if status == 503 or "unavailable" in detail:
        return "Spotify is temporarily unavailable, Sir. Try again shortly."
    if "no active device" in detail or "device" in detail:
        return "No active Spotify device found, Sir. Open Spotify on a device first."
    return "Spotify encountered an error, Sir. Make sure it's open and you're logged in."