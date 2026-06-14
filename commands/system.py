"""PC system commands — each command type is a separate handler (Strategy pattern).

To add a new command: subclass _CommandHandler, append an instance to _COMMAND_HANDLERS.
handle_command() itself never needs to change (Open/Closed Principle).
"""

import webbrowser
import subprocess
import os
import re
import datetime
import threading
import logging

import psutil
import pyautogui

from commands.notes import read_notes

log = logging.getLogger("hades.commands.system")

# ── pycaw (optional — Windows volume control) ─────────────────────────────────
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

LOCAL_APPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))

APPS: dict[str, str] = {
    "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "spotify":      os.path.join(LOCAL_APPDATA, "Microsoft", "WindowsApps", "Spotify.exe"),
    "notepad":      "notepad.exe",
    "calculator":   "calc.exe",
    "vscode":       os.path.join(LOCAL_APPDATA, "Programs", "Microsoft VS Code", "Code.exe"),
    "explorer":     "explorer.exe",
    "task manager": "taskmgr.exe",
    "word":         r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
}

WEBSITES: dict[str, str] = {
    "youtube":   "https://youtube.com",
    "google":    "https://google.com",
    "github":    "https://github.com",
    "gmail":     "https://mail.google.com",
    "linkedin":  "https://linkedin.com",
    "reddit":    "https://reddit.com",
    "twitter":   "https://twitter.com",
    "instagram": "https://instagram.com",
    "netflix":   "https://netflix.com",
}


# ── Shared helpers ────────────────────────────────────────────────────────────

def set_volume(level: int):
    if not PYCAW_AVAILABLE:
        return "pycaw not installed (or not on Windows), Sir."
    speakers  = AudioUtilities.GetSpeakers()
    dev       = getattr(speakers, "_dev", speakers)
    interface = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume    = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(level / 100, None)


def set_reminder(text: str, seconds: int):
    def _remind():
        import time
        time.sleep(seconds)
        from voice.tts import speak
        speak(f"Sir, reminder: {text}")
        log.info("REMINDER: %s", text)
    threading.Thread(target=_remind, daemon=True).start()


# ── Strategy base class ───────────────────────────────────────────────────────

class _CommandHandler:
    """Base for command handlers. Subclass, override can_handle + handle, register in _COMMAND_HANDLERS."""
    def can_handle(self, text: str, lower: str) -> bool:
        raise NotImplementedError
    def handle(self, text: str, lower: str) -> str | None:
        raise NotImplementedError


# ── Concrete command handlers (one class = one responsibility) ────────────────

class _VolumeHandler(_CommandHandler):
    def can_handle(self, text, lower):
        return (bool(re.search(r"volume.*?\d+", lower)) or
                any(w in lower for w in ("volume up", "volume down", "mute")))
    def handle(self, text, lower):
        m = re.search(r"volume.*?(\d+)", lower)
        if m:
            level = max(0, min(100, int(m.group(1))))
            set_volume(level)
            return f"Volume set to {level}%, Sir."
        if "volume up" in lower:
            pyautogui.press("volumeup", presses=5)
            return "Volume increased, Sir."
        if "volume down" in lower:
            pyautogui.press("volumedown", presses=5)
            return "Volume decreased, Sir."
        if "mute" in lower:
            pyautogui.press("volumemute")
            return "Muted, Sir."
        return None


class _TimeHandler(_CommandHandler):
    _TIME = ("what time", "what's the time", "current time",
             "tell me the time", "what is the time")
    _DATE = ("what date", "what's the date", "current date",
             "today's date", "what day is it", "what is today")
    def can_handle(self, text, lower):
        return any(p in lower for p in self._TIME + self._DATE)
    def handle(self, text, lower):
        if any(p in lower for p in self._TIME):
            return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}, Sir."
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}, Sir."


class _BatteryHandler(_CommandHandler):
    def can_handle(self, text, lower):
        return "battery" in lower
    def handle(self, text, lower):
        battery = psutil.sensors_battery()
        if battery:
            status = "charging" if battery.power_plugged else "on battery"
            return f"Battery is at {int(battery.percent)}% and {status}, Sir."
        return "Could not read battery status, Sir."


class _ScreenshotHandler(_CommandHandler):
    def can_handle(self, text, lower):
        return "screenshot" in lower
    def handle(self, text, lower):
        path = os.path.expanduser("~/Desktop/screenshot.png")
        pyautogui.screenshot(path)
        return "Screenshot saved to your Desktop, Sir."


class _ClipboardHandler(_CommandHandler):
    def can_handle(self, text, lower):
        return "clipboard" in lower or "what did i copy" in lower
    def handle(self, text, lower):
        import pyperclip
        return f"Your clipboard contains: {pyperclip.paste()[:200]}"


class _PowerHandler(_CommandHandler):
    _KEYWORDS = ("cancel shutdown", "shutdown", "shut down", "restart", "lock")
    def can_handle(self, text, lower):
        return any(w in lower for w in self._KEYWORDS)
    def handle(self, text, lower):
        if "cancel shutdown" in lower:
            os.system("shutdown /a")
            return "Shutdown cancelled, Sir."
        if "shutdown" in lower or "shut down" in lower:
            m = re.search(r"(\d+)\s*minute", lower)
            seconds = int(m.group(1)) * 60 if m else 0
            os.system(f"shutdown /s /t {seconds}")
            mins = f"in {m.group(1)} minutes" if m else "now"
            return f"Shutting down {mins}, Sir."
        if "restart" in lower:
            os.system("shutdown /r /t 5")
            return "Restarting in 5 seconds, Sir."
        if "lock" in lower:
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return "Workstation locked, Sir."
        return None


class _NotesReadHandler(_CommandHandler):
    def can_handle(self, text, lower):
        return "read my notes" in lower or "show my notes" in lower or "read notes" in lower
    def handle(self, text, lower):
        m = re.search(r"(?:about|under|for|in)\s+([a-zA-Z]+)", lower)
        return read_notes(m.group(1) if m else None)


class _ReminderHandler(_CommandHandler):
    _PATTERN = re.compile(r"remind me in (\d+) (second|minute|hour)s?(?:\s+to\s+(.+))?")
    def can_handle(self, text, lower):
        return bool(self._PATTERN.search(lower))
    def handle(self, text, lower):
        m      = self._PATTERN.search(lower)
        amount = int(m.group(1))
        unit   = m.group(2)
        task   = (m.group(3) or "reminder").strip()
        mult   = {"second": 1, "minute": 60, "hour": 3600}[unit]
        set_reminder(task, amount * mult)
        return f"I'll remind you in {amount} {unit}{'s' if amount != 1 else ''}, Sir."


class _WebSearchHandler(_CommandHandler):
    def can_handle(self, text, lower):
        return "search for" in lower or "google" in lower
    def handle(self, text, lower):
        query = re.sub(r".*(search for|google)[:\s]*", "", lower).strip()
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return f"Searching for {query}, Sir."


class _WebsiteHandler(_CommandHandler):
    def can_handle(self, text, lower):
        return any(site in lower for site in WEBSITES)
    def handle(self, text, lower):
        for site, url in WEBSITES.items():
            if site in lower:
                webbrowser.open(url)
                return f"Opening {site}, Sir."
        return None


class _AppHandler(_CommandHandler):
    def can_handle(self, text, lower):
        return any(app in lower for app in APPS)
    def handle(self, text, lower):
        for app, path in APPS.items():
            if app in lower:
                try:
                    subprocess.Popen(path)
                    return f"Opening {app}, Sir."
                except FileNotFoundError:
                    return f"Could not find {app} at the expected path, Sir."
        return None


class _SystemInfoHandler(_CommandHandler):
    _KEYWORDS = ("cpu", "processor", "ram", "memory usage", "disk", "storage")
    def can_handle(self, text, lower):
        return any(w in lower for w in self._KEYWORDS)
    def handle(self, text, lower):
        if "cpu" in lower or "processor" in lower:
            return f"CPU usage is at {psutil.cpu_percent(interval=1)}%, Sir."
        if "ram" in lower or "memory usage" in lower:
            ram = psutil.virtual_memory()
            return (f"RAM usage is {ram.percent}%, "
                    f"with {round(ram.available / (1024**3), 1)}GB available, Sir.")
        if "disk" in lower or "storage" in lower:
            disk = psutil.disk_usage("/")
            return (f"Disk usage is {disk.percent}%, "
                    f"with {round(disk.free / (1024**3), 1)}GB free, Sir.")
        return None


# ── Handler registry — position defines priority ──────────────────────────────

_COMMAND_HANDLERS: list[_CommandHandler] = [
    _VolumeHandler(),
    _TimeHandler(),
    _BatteryHandler(),
    _ScreenshotHandler(),
    _ClipboardHandler(),
    _PowerHandler(),
    _NotesReadHandler(),
    _ReminderHandler(),
    _WebSearchHandler(),
    _WebsiteHandler(),
    _AppHandler(),
    _SystemInfoHandler(),
]


# ── Dispatcher ────────────────────────────────────────────────────────────────

def handle_command(text: str) -> str | None:
    """Dispatch text to the first matching command handler; return None if unrecognised."""
    lower = text.lower()
    for handler in _COMMAND_HANDLERS:
        if handler.can_handle(text, lower):
            result = handler.handle(text, lower)
            if result is not None:
                return result
    return None
