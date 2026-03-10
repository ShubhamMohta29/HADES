import webbrowser
import subprocess
import os
import re
import datetime
import psutil
import pyautogui
import threading

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
        return f"pycaw not installed. Run: pip install pycaw"
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(level / 100, None)

# ── Apps & websites ─────────────────────────────────────────────────────────
APPS = {
    "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "spotify":      os.path.expanduser(r"C:\Users\shubh\AppData\Local\Microsoft\WindowsApps\Spotify.exe"),
    "notepad":      "notepad.exe",
    "calculator":   "calc.exe",
    "vscode":       os.path.expanduser(r"~\AppData\Local\Programs\Microsoft VS Code\Code.exe"),
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
reminders = []

def set_reminder(text, seconds):
    def _remind():
        import time
        time.sleep(seconds)
        from voice import speak
        speak(f"Sir, reminder: {text}")
        print(f"⏰ REMINDER: {text}")
    threading.Thread(target=_remind, daemon=True).start()

# ── Notes ───────────────────────────────────────────────────────────────────
NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")

def save_note(note):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(NOTES_FILE, "a") as f:
        f.write(f"[{timestamp}] {note}\n")

def read_notes():
    if not os.path.exists(NOTES_FILE):
        return "No notes found, Sir."
    with open(NOTES_FILE, "r") as f:
        content = f.read().strip()
    return content if content else "Your notes are empty, Sir."

# ── Main command handler ─────────────────────────────────────────────────────
def handle_command(text):
    t = text.lower()

    # ── Volume ──────────────────────────────────────────────────────────────
    match = re.search(r'volume.*?(\d+)', t)
    if match:
        level = max(0, min(100, int(match.group(1))))
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
    if "time" in t:
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"The time is {now}, Sir."
    if "date" in t:
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {today}, Sir."

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
        return f"Screenshot saved to your Desktop, Sir."

    # ── Clipboard ───────────────────────────────────────────────────────────
    if "clipboard" in t or "what did i copy" in t:
        import pyperclip
        content = pyperclip.paste()
        return f"Your clipboard contains: {content[:200]}"

    # ── PC power ────────────────────────────────────────────────────────────
    if "shutdown" in t or "shut down" in t:
        match = re.search(r'(\d+)\s*minute', t)
        seconds = int(match.group(1)) * 60 if match else 0
        os.system(f"shutdown /s /t {seconds}")
        mins = f"in {match.group(1)} minutes" if match else "now"
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

    # ── Notes ───────────────────────────────────────────────────────────────
    if "make a note" in t or "take a note" in t or "note that" in t:
        note = re.sub(r'.*(note that|make a note|take a note)[:\s]*', '', t).strip()
        if note:
            save_note(note)
            return f"Note saved, Sir."
    if "read my notes" in t or "show my notes" in t:
        return read_notes()

    # ── Reminders ───────────────────────────────────────────────────────────
    # "remind me in 10 minutes to call mom"
    match = re.search(r'remind me in (\d+) (minute|hour|second)', t)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        seconds = amount * (60 if unit == "minute" else 3600 if unit == "hour" else 1)
        task = re.sub(r'.*remind me in \d+ (minute|hour|second)s? ?(to)?', '', t).strip()
        set_reminder(task or "reminder", seconds)
        return f"I'll remind you in {amount} {unit}{'s' if amount > 1 else ''}, Sir."

    # ── Search web ──────────────────────────────────────────────────────────
    if "search for" in t or "google" in t:
        query = re.sub(r'.*(search for|google)[:\s]*', '', t).strip()
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return f"Searching for {query}, Sir."

    # ── Open websites ────────────────────────────────────────────────────────
    for site, url in WEBSITES.items():
        if site in t:
            webbrowser.open(url)
            return f"Opening {site}, Sir."

    # ── Open apps ────────────────────────────────────────────────────────────
    for app, path in APPS.items():
        if app in t:
            try:
                subprocess.Popen(path)
                return f"Opening {app}, Sir."
            except FileNotFoundError:
                return f"Could not find {app} at the expected path, Sir."

    # ── System info ─────────────────────────────────────────────────────────
    if "cpu" in t or "processor" in t:
        cpu = psutil.cpu_percent(interval=1)
        return f"CPU usage is at {cpu}%, Sir."
    if "ram" in t or "memory usage" in t:
        ram = psutil.virtual_memory()
        return f"RAM usage is {ram.percent}%, with {round(ram.available / (1024**3), 1)}GB available, Sir."
    if "disk" in t or "storage" in t:
        disk = psutil.disk_usage('/')
        return f"Disk usage is {disk.percent}%, with {round(disk.free / (1024**3), 1)}GB free, Sir."

    return None  # No command matched — send to AI