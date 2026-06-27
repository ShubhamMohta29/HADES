"""HADES GUI — pywebview frontend with a glowing orb and chat log.

The Python side exposes a JS-callable API via the `HadesAPI` class.
The web UI posts user messages back through `window.pywebview.api.send_message(text)`.

Auth flow (when Supabase is configured):
  1. Window loads → _on_loaded() fires.
  2. If ~/.jarvis/session.json has a valid token, restore it silently and fire
     on_auth_complete(user_id).
  3. Otherwise the login panel (already visible in the HTML) waits for the
     user to enter credentials; JS calls api.login() → on_auth_complete fires.
  4. If Supabase is NOT configured, the login panel is hidden immediately and
     on_auth_complete(None) fires so the main loop starts in local mode.
"""

import json
import logging
import threading
from pathlib import Path

import webview

log = logging.getLogger("hades.gui")

FRONTEND_DIR = Path(__file__).parent / "frontend"
INDEX_HTML   = FRONTEND_DIR / "index.html"
SESSION_FILE = Path.home() / ".jarvis" / "session.json"


# ── Session persistence ───────────────────────────────────────────────────────

def _save_session(session: dict):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session, f)
    except Exception as e:
        log.warning("Could not save session: %s", e)


def _load_session() -> dict | None:
    if not SESSION_FILE.exists():
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ── JS API ────────────────────────────────────────────────────────────────────

class HadesAPI:
    """Bridge exposed to the JS side as `pywebview.api`."""

    def __init__(self):
        self.on_text_command = None   # set externally by main.py
        self.on_auth_complete = None  # set externally by main.py
        self._window = None           # set by HadesGUI after window creation

    def send_message(self, text: str):
        """Called from JS when user types in the input bar."""
        if callable(self.on_text_command):
            threading.Thread(
                target=self.on_text_command, args=(text,), daemon=True
            ).start()
        return {"ok": True}

    def login(self, email: str, password: str):
        """Called from JS when user submits the login form."""
        try:
            import db
            session = db.sign_in(email, password)
            _save_session(session)
            user_data = session.get("user") or {}
            user_id = user_data.get("id") if isinstance(user_data, dict) else None
            if self._window:
                self._window.evaluate_js("window.skipLogin()")
            if callable(self.on_auth_complete):
                threading.Thread(
                    target=self.on_auth_complete, args=(user_id,), daemon=True
                ).start()
        except Exception as e:
            log.warning("Login failed: %s", e)
            if self._window:
                self._window.evaluate_js(f"window.showLoginError({json.dumps('Authentication failed. Please check your credentials and try again.')})")
        return {"ok": True}

    def register(self, email: str, password: str):
        """Called from JS when user submits the sign-up form."""
        try:
            import db
            result = db.sign_up(email, password)
            if result.get("pending_confirmation"):
                if self._window:
                    self._window.evaluate_js("window.showSignupPending()")
                return {"ok": True}
            _save_session(result)
            user_data = result.get("user") or {}
            user_id = user_data.get("id") if isinstance(user_data, dict) else None
            if self._window:
                self._window.evaluate_js("window.skipLogin()")
            if callable(self.on_auth_complete):
                threading.Thread(
                    target=self.on_auth_complete, args=(user_id,), daemon=True
                ).start()
        except Exception as e:
            log.warning("Registration failed: %s", e)
            if self._window:
                self._window.evaluate_js(f"window.showSignupError({json.dumps('Registration failed. Please try again or use a different email.')})")
        return {"ok": True}

    def magic_link(self, email: str):
        """Called from JS when user requests a passwordless magic-link email."""
        try:
            import db
            db.sign_in_magic_link(email)
            if self._window:
                self._window.evaluate_js("window.showMagicLinkSent()")
        except Exception as e:
            log.warning("Magic link failed: %s", e)
            if self._window:
                self._window.evaluate_js(f"window.showLoginError({json.dumps('Could not send magic link. Please check your email and try again.')})")
        return {"ok": True}

    def skip_login(self):
        """User chose local mode (no Supabase)."""
        if callable(self.on_auth_complete):
            threading.Thread(
                target=self.on_auth_complete, args=(None,), daemon=True
            ).start()
        return {"ok": True}


# ── GUI ───────────────────────────────────────────────────────────────────────

class HadesGUI:
    """pywebview window wrapper with auth, status, and chat helpers."""

    def __init__(self):
        self.api = HadesAPI()
        self._window = webview.create_window(
            "H.A.D.E.S",
            url=str(INDEX_HTML),
            js_api=self.api,
            width=560,
            height=880,
            resizable=True,
            background_color="#020408",
        )
        self.api._window = self._window
        self.root = _RootShim(self._window)

        # Wire the loaded event for auto-login / session restore
        self._window.events.loaded += self._on_loaded

    def _on_loaded(self):
        """Fires once the webview has finished loading index.html."""
        try:
            import db
            if not db.is_available():
                self._js("window.skipLogin()")
                if callable(self.api.on_auth_complete):
                    threading.Thread(
                        target=self.api.on_auth_complete, args=(None,), daemon=True
                    ).start()
                return

            # Try to restore an existing session token
            session = _load_session()
            if session:
                access_token  = session.get("access_token", "")
                refresh_token = session.get("refresh_token", "")
                if access_token and refresh_token:
                    user_id = db.restore_session(access_token, refresh_token)
                    if user_id:
                        self._js("window.skipLogin()")
                        if callable(self.api.on_auth_complete):
                            threading.Thread(
                                target=self.api.on_auth_complete, args=(user_id,), daemon=True
                            ).start()
                        return

            # No valid session — login panel is already visible in the HTML
        except Exception as e:
            log.warning("_on_loaded error: %s", e)
            # Fall back to local mode so the app isn't permanently stuck
            self._js("window.skipLogin()")
            if callable(self.api.on_auth_complete):
                threading.Thread(
                    target=self.api.on_auth_complete, args=(None,), daemon=True
                ).start()

    # ── Properties that main.py sets ─────────────────────────────────────────

    @property
    def on_text_command(self):
        return self.api.on_text_command

    @on_text_command.setter
    def on_text_command(self, fn):
        self.api.on_text_command = fn

    @property
    def on_auth_complete(self):
        return self.api.on_auth_complete

    @on_auth_complete.setter
    def on_auth_complete(self, fn):
        self.api.on_auth_complete = fn

    # ── JS helpers ────────────────────────────────────────────────────────────

    def _js(self, code: str):
        try:
            self._window.evaluate_js(code)
        except Exception as e:
            log.debug("evaluate_js failed: %s", e)

    def add_message(self, who: str, text: str):
        self._js(f"window.addMessage({json.dumps(who)}, {json.dumps(text)});")

    def add_system_message(self, text: str):
        self._js(f"window.addSystemMessage({json.dumps(text)});")

    def set_status(self, status: str):
        self._js(f"window.setStatus({json.dumps(status)});")

    def add_help_card(self, html: str):
        self._js(f"window.addHelpCard({json.dumps(html)});")


class _RootShim:
    """Mimics the old `gui.root` Tk object — only mainloop() is used."""

    def __init__(self, window):
        self._window = window

    def mainloop(self):
        webview.start(debug=False)
