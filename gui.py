"""HADES GUI — pywebview frontend with a glowing orb and chat log.

The Python side exposes a JS-callable API via the `HadesAPI` class.
The web UI posts user messages back through `window.pywebview.api.send_message(text)`.
"""

import json
import logging
import threading
from pathlib import Path

import webview

log = logging.getLogger("hades.gui")

FRONTEND_DIR = Path(__file__).parent / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"


class HadesAPI:
    """Bridge exposed to the JS side as `pywebview.api`."""

    def __init__(self):
        self.on_text_command = None  # set externally by main.py

    def send_message(self, text: str):
        """Called from JS when user types in the input bar."""
        if callable(self.on_text_command):
            # Run in a thread so JS call returns immediately
            threading.Thread(
                target=self.on_text_command, args=(text,), daemon=True
            ).start()
        return {"ok": True}


class HadesGUI:
    """Drop-in replacement for the old Tkinter HadesGUI.

    Public surface kept identical so main.py doesn't need changes:
      - self.root.mainloop()     → starts webview
      - self.add_message(who, text)
      - self.add_system_message(text)
      - self.set_status(status)  → "standby" | "listening" | "thinking" | "speaking"
      - self.on_text_command     → callable(text) set by main.py
    """

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

        # Shim so `gui.root.mainloop()` still works
        self.root = _RootShim(self._window)

    # ── Property that main.py sets ──────────────────────────────────────────
    @property
    def on_text_command(self):
        return self.api.on_text_command

    @on_text_command.setter
    def on_text_command(self, fn):
        self.api.on_text_command = fn

    # ── JS-side helpers ─────────────────────────────────────────────────────
    def _js(self, code: str):
        try:
            self._window.evaluate_js(code)
        except Exception as e:
            log.debug("evaluate_js failed: %s", e)

    def add_message(self, who: str, text: str):
        self._js(
            f"window.addMessage({json.dumps(who)}, {json.dumps(text)});"
        )

    def add_system_message(self, text: str):
        self._js(f"window.addSystemMessage({json.dumps(text)});")

    def set_status(self, status: str):
        self._js(f"window.setStatus({json.dumps(status)});")


class _RootShim:
    """Mimics the old `gui.root` Tk object — only mainloop() is used."""

    def __init__(self, window):
        self._window = window

    def mainloop(self):
        # `debug=False` disables the right-click menu and dev tools
        webview.start(debug=False)
