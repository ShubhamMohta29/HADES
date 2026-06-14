"""PC system commands: volume, apps, power, time, battery, reminders, web search."""

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

# ── Volume ───────────────────────────────────────────────────────────────────
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


def handle_command(text: str):
    t = text.lower()

    # ── Volume ───────────────────────────────────────────────────────────────
    m = re.search(r"volume.*?(\d+)", t)
    if m:
        level = max(0, min(100, int(m.group(1))))
        set_volume(level)
        return f"Volume set to {level}%, Sir."
    if "volume up" in t:
        pyautogui.press("volumeup", presses=5)
        return "Volume increased, Sir."
    if "volume down" in t:
        pyautogui.press("volumedown", presses=5)
        return "Volume decreased, Sir."
    if "mute" in t:
        pyautogui.press("volumemute")
        return "Muted, Sir."

    # ── Time & Date ──────────────────────────────────────────────────────────
    time_phrases = ["what time", "what's the time", "current time",
                    "tell me the time", "what is the time"]
    date_phrases = ["what date", "what's the date", "current date",
                    "today's date", "what day is it", "what is today"]
    if any(p in t for p in time_phrases):
        return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}, Sir."
    if any(p in t for p in date_phrases):
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}, Sir."

    # ── Battery ──────────────────────────────────────────────────────────────
    if "battery" in t:
        battery = psutil.sensors_battery()
        if battery:
            status = "charging" if battery.power_plugged else "on battery"
            return f"Battery is at {int(battery.percent)}% and {status}, Sir."
        return "Could not read battery status, Sir."

    # ── Screenshot ───────────────────────────────────────────────────────────
    if "screenshot" in t:
        path = os.path.expanduser("~/Desktop/screenshot.png")
        pyautogui.screenshot(path)
        return "Screenshot saved to your Desktop, Sir."

    # ── Clipboard ────────────────────────────────────────────────────────────
    if "clipboard" in t or "what did i copy" in t:
        import pyperclip
        content = pyperclip.paste()
        return f"Your clipboard contains: {content[:200]}"

    # ── PC power ─────────────────────────────────────────────────────────────
    if "shutdown" in t or "shut down" in t:
        m = re.search(r"(\d+)\s*minute", t)
        seconds = int(m.group(1)) * 60 if m else 0
        os.system(f"shutdown /s /t {seconds}")
        mins = f"in {m.group(1)} minutes" if m else "now"
        return f"Shutting down {mins}, Sir."
    if "restart" in t:
        os.system("shutdown /r /t 5")
        return "Restarting in 5 seconds, Sir."
    if "lock" in t:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Workstation locked, Sir."
    if "cancel shutdown" in t:
        os.system("shutdown /a")
        return "Shutdown cancelled, Sir."

    # ── Notes (read only — saving is handled conversationally in router.py) ──
    if "read my notes" in t or "show my notes" in t or "read notes" in t:
        m = re.search(r"(?:about|under|for|in)\s+([a-zA-Z]+)", t)
        category = m.group(1) if m else None
        return read_notes(category)

    # ── Reminders ────────────────────────────────────────────────────────────
    m = re.search(r"remind me in (\d+) (second|minute|hour)s?(?:\s+to\s+(.+))?", t)
    if m:
        amount = int(m.group(1))
        unit   = m.group(2)
        task   = (m.group(3) or "reminder").strip()
        mult   = {"second": 1, "minute": 60, "hour": 3600}[unit]
        set_reminder(task, amount * mult)
        return f"I'll remind you in {amount} {unit}{'s' if amount != 1 else ''}, Sir."

    # ── Web search ───────────────────────────────────────────────────────────
    if "search for" in t or "google" in t:
        query = re.sub(r".*(search for|google)[:\s]*", "", t).strip()
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return f"Searching for {query}, Sir."

    # ── Websites ─────────────────────────────────────────────────────────────
    for site, url in WEBSITES.items():
        if site in t:
            webbrowser.open(url)
            return f"Opening {site}, Sir."

    # ── Apps ─────────────────────────────────────────────────────────────────
    for app, path in APPS.items():
        if app in t:
            try:
                subprocess.Popen(path)
                return f"Opening {app}, Sir."
            except FileNotFoundError:
                return f"Could not find {app} at the expected path, Sir."

    # ── System info ──────────────────────────────────────────────────────────
    if "cpu" in t or "processor" in t:
        return f"CPU usage is at {psutil.cpu_percent(interval=1)}%, Sir."
    if "ram" in t or "memory usage" in t:
        ram = psutil.virtual_memory()
        return f"RAM usage is {ram.percent}%, with {round(ram.available / (1024**3), 1)}GB available, Sir."
    if "disk" in t or "storage" in t:
        disk = psutil.disk_usage("/")
        return f"Disk usage is {disk.percent}%, with {round(disk.free / (1024**3), 1)}GB free, Sir."

    return None
