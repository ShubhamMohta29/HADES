"""PC control commands: volume, apps, time, battery, reminders, notes, etc.

Notes format on disk: [YYYY-MM-DD HH:MM] [category] note text
Category is optional — omitted for uncategorised notes.
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

log = logging.getLogger("hades.commands")

# ── Volume control ──────────────────────────────────────────────────────────
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False


def set_volume(level):
    if not PYCAW_AVAILABLE:
        return "pycaw not installed (or not on Windows), Sir."
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(level / 100, None)


# ── Apps & websites ─────────────────────────────────────────────────────────
# Use %USERNAME% expansion + env LOCALAPPDATA for portability.
LOCAL_APPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))

APPS = {
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

WEBSITES = {
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

# ── Reminders ───────────────────────────────────────────────────────────────
def set_reminder(text, seconds):
    def _remind():
        import time
        time.sleep(seconds)
        from voice import speak
        speak(f"Sir, reminder: {text}")
        log.info("⏰ REMINDER: %s", text)
    threading.Thread(target=_remind, daemon=True).start()


# ── Notes ───────────────────────────────────────────────────────────────────
NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")


def save_note(note: str, category: str = None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    cat_str = f"[{category.lower()}] " if category else ""
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {cat_str}{note}\n")


def get_existing_categories() -> list:
    """Return all unique category tags found in notes.txt, defaulting to ['personal', 'work']."""
    if not os.path.exists(NOTES_FILE):
        return ["personal", "work"]
    cats = set()
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            # Category tag is letters-only in brackets, appearing after the timestamp
            # e.g. "[2025-05-17 14:32] [work] ..."  → match [work]
            m = re.search(r"\]\s*\[([a-zA-Z]+)\]", line)
            if m:
                cats.add(m.group(1).lower())
    return sorted(cats) if cats else ["personal", "work"]


def read_notes(category: str = None) -> str:
    if not os.path.exists(NOTES_FILE):
        return "No notes found, Sir."
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        lines = [l.rstrip() for l in f if l.strip()]
    if not lines:
        return "Your notes are empty, Sir."
    if category:
        tag = f"[{category.lower()}]"
        filtered = [l for l in lines if tag in l.lower()]
        if not filtered:
            return f"No notes found under '{category}', Sir."
        # Strip timestamp + category tag for clean spoken output
        clean = []
        for l in filtered:
            l = re.sub(r"^\[[^\]]+\]\s*", "", l)   # remove timestamp
            l = re.sub(r"^\[[^\]]+\]\s*", "", l)   # remove category tag
            clean.append(l.strip())
        return f"Your {category} notes: " + "; ".join(clean) + "."
    return "\n".join(lines)


# ── Main command handler ────────────────────────────────────────────────────
def handle_command(text):
    t = text.lower()

    # ── Volume ──────────────────────────────────────────────────────────────
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

    # ── Time & Date ─────────────────────────────────────────────────────────
    time_phrases = ["what time", "what's the time", "current time",
                    "tell me the time", "what is the time"]
    date_phrases = ["what date", "what's the date", "current date",
                    "today's date", "what day is it", "what is today"]
    if any(p in t for p in time_phrases):
        return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}, Sir."
    if any(p in t for p in date_phrases):
        return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}, Sir."

    # ── Battery ─────────────────────────────────────────────────────────────
    if "battery" in t:
        battery = psutil.sensors_battery()
        if battery:
            status = "charging" if battery.power_plugged else "on battery"
            return f"Battery is at {int(battery.percent)}% and {status}, Sir."
        return "Could not read battery status, Sir."

    # ── Screenshot ──────────────────────────────────────────────────────────
    if "screenshot" in t:
        path = os.path.expanduser("~/Desktop/screenshot.png")
        pyautogui.screenshot(path)
        return "Screenshot saved to your Desktop, Sir."

    # ── Clipboard ───────────────────────────────────────────────────────────
    if "clipboard" in t or "what did i copy" in t:
        import pyperclip
        content = pyperclip.paste()
        return f"Your clipboard contains: {content[:200]}"

    # ── PC power ────────────────────────────────────────────────────────────
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

    # ── Notes (read only — saving is handled conversationally in main.route()) ─
    if "read my notes" in t or "show my notes" in t or "read notes" in t:
        m = re.search(r"(?:about|under|for|in)\s+([a-zA-Z]+)", t)
        category = m.group(1) if m else None
        return read_notes(category)

    # ── Reminders ───────────────────────────────────────────────────────────
    # "remind me in 10 minutes to call mom"
    m = re.search(
        r"remind me in (\d+) (second|minute|hour)s?(?:\s+to\s+(.+))?",
        t,
    )
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        task = (m.group(3) or "reminder").strip()
        mult = {"second": 1, "minute": 60, "hour": 3600}[unit]
        set_reminder(task, amount * mult)
        return f"I'll remind you in {amount} {unit}{'s' if amount != 1 else ''}, Sir."

    # ── Search web ──────────────────────────────────────────────────────────
    if "search for" in t or "google" in t:
        query = re.sub(r".*(search for|google)[:\s]*", "", t).strip()
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return f"Searching for {query}, Sir."

    # ── Open websites ───────────────────────────────────────────────────────
    for site, url in WEBSITES.items():
        if site in t:
            webbrowser.open(url)
            return f"Opening {site}, Sir."

    # ── Open apps ───────────────────────────────────────────────────────────
    for app, path in APPS.items():
        if app in t:
            try:
                subprocess.Popen(path)
                return f"Opening {app}, Sir."
            except FileNotFoundError:
                return f"Could not find {app} at the expected path, Sir."

    # ── System info ─────────────────────────────────────────────────────────
    if "cpu" in t or "processor" in t:
        return f"CPU usage is at {psutil.cpu_percent(interval=1)}%, Sir."
    if "ram" in t or "memory usage" in t:
        ram = psutil.virtual_memory()
        return f"RAM usage is {ram.percent}%, with {round(ram.available / (1024**3), 1)}GB available, Sir."
    if "disk" in t or "storage" in t:
        disk = psutil.disk_usage("/")
        return f"Disk usage is {disk.percent}%, with {round(disk.free / (1024**3), 1)}GB free, Sir."

    return None  # fall through to AI


# ── Help card HTML ──────────────────────────────────────────────────────────
# Rendered inside the chat panel via gui.add_help_card(). Styled by .help-card CSS.
HELP_HTML = """<div class="help-card">
  <div class="help-title">&#9670;&nbsp; COMMAND REFERENCE</div>

  <div class="help-cat">ACTIVATION</div>
  <div class="help-row"><span class="help-cmd">"HADES"</span><span class="help-desc">wake word</span></div>
  <div class="help-row"><span class="help-cmd">"sleep" / "goodbye" / "stand by"</span><span class="help-desc">enter standby mode</span></div>
  <div class="help-row"><span class="help-cmd">"clear memory"</span><span class="help-desc">reset AI conversation history</span></div>
  <div class="help-row"><span class="help-cmd">"help" / "commands"</span><span class="help-desc">show this reference</span></div>

  <div class="help-cat">INFORMATION</div>
  <div class="help-row"><span class="help-cmd">"weather in [city]"</span><span class="help-desc">current conditions &amp; temp</span></div>
  <div class="help-row"><span class="help-cmd">"news" / "news about [topic]"</span><span class="help-desc">top headlines</span></div>
  <div class="help-row"><span class="help-cmd">"[ticker] stock"</span><span class="help-desc">live stock price</span></div>
  <div class="help-row"><span class="help-cmd">"bitcoin" / "ethereum" / "solana"</span><span class="help-desc">crypto price</span></div>

  <div class="help-cat">SPOTIFY</div>
  <div class="help-row"><span class="help-cmd">"play [song / artist]"</span><span class="help-desc">search and play track</span></div>
  <div class="help-row"><span class="help-cmd">"play my liked songs"</span><span class="help-desc">play liked songs</span></div>
  <div class="help-row"><span class="help-cmd">"play [name] playlist"</span><span class="help-desc">play a specific playlist</span></div>
  <div class="help-row"><span class="help-cmd">"pause" / "skip" / "previous"</span><span class="help-desc">playback control</span></div>
  <div class="help-row"><span class="help-cmd">"what's playing"</span><span class="help-desc">current track info</span></div>
  <div class="help-row"><span class="help-cmd">"shuffle"</span><span class="help-desc">toggle shuffle</span></div>

  <div class="help-cat">PC CONTROL</div>
  <div class="help-row"><span class="help-cmd">"set volume to [%]" / "mute"</span><span class="help-desc">audio control</span></div>
  <div class="help-row"><span class="help-cmd">"open chrome" / "open vscode"</span><span class="help-desc">launch app</span></div>
  <div class="help-row"><span class="help-cmd">"open youtube" / "open github"</span><span class="help-desc">open website</span></div>
  <div class="help-row"><span class="help-cmd">"search for [query]"</span><span class="help-desc">Google search in browser</span></div>
  <div class="help-row"><span class="help-cmd">"screenshot"</span><span class="help-desc">save to Desktop</span></div>
  <div class="help-row"><span class="help-cmd">"battery" / "cpu" / "ram" / "disk"</span><span class="help-desc">system status</span></div>
  <div class="help-row"><span class="help-cmd">"shutdown" / "restart" / "lock"</span><span class="help-desc">power control</span></div>
  <div class="help-row"><span class="help-cmd">"clipboard"</span><span class="help-desc">read clipboard contents</span></div>

  <div class="help-cat">UTILITIES</div>
  <div class="help-row"><span class="help-cmd">"take a note: [text]"</span><span class="help-desc">save a note (asks category)</span></div>
  <div class="help-row"><span class="help-cmd">"read my [category] notes"</span><span class="help-desc">view notes by category</span></div>
  <div class="help-row"><span class="help-cmd">"remind me in [N] mins to [task]"</span><span class="help-desc">timed reminder</span></div>
  <div class="help-row"><span class="help-cmd">"what time is it" / "what's today"</span><span class="help-desc">time &amp; date</span></div>

  <div class="help-cat">SCREEN VISION</div>
  <div class="help-row"><span class="help-cmd">"what's on my screen"</span><span class="help-desc">AI screen analysis</span></div>
  <div class="help-row"><span class="help-cmd">"help me with my homework"</span><span class="help-desc">screen-aware assistance</span></div>
</div>"""
