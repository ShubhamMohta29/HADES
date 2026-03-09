"""
Spotify control via spotipy.
Setup:
  1. pip install spotipy
  2. Go to https://developer.spotify.com/dashboard → create app
  3. Set redirect URI to http://localhost:8888/callback
  4. Add SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI to .env
"""
try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="user-modify-playback-state user-read-playback-state user-read-currently-playing"
    ))
    SPOTIFY_AVAILABLE = True
except Exception:
    SPOTIFY_AVAILABLE = False

def spotify_command(text):
    if not SPOTIFY_AVAILABLE:
        return "Spotify is not configured, Sir. Please add your Spotify API credentials."

    t = text.lower()
    try:
        if "play" in t and "spotify" not in t:
            query = t.replace("play", "").strip()
            results = sp.search(q=query, limit=1, type="track")
            tracks = results["tracks"]["items"]
            if tracks:
                sp.start_playback(uris=[tracks[0]["uri"]])
                return f"Playing {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}, Sir."
            return f"Could not find {query} on Spotify, Sir."

        if "pause" in t or "stop music" in t:
            sp.pause_playback()
            return "Music paused, Sir."

        if "resume" in t or "continue" in t:
            sp.start_playback()
            return "Resuming music, Sir."

        if "next" in t or "skip" in t:
            sp.next_track()
            return "Skipping to next track, Sir."

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
        return f"Spotify error: {e}. Make sure Spotify is open on a device, Sir."

    return None