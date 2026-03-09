import tkinter as tk
from tkinter import scrolledtext, font
import datetime

class HadesGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("H.A.D.E.S")
        self.root.geometry("500x700")
        self.root.configure(bg="#0a0a0f")
        self.root.resizable(False, False)

        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg="#0d1117", pady=10)
        header.pack(fill=tk.X)

        title_font = font.Font(family="Consolas", size=16, weight="bold")
        tk.Label(header, text="◈  H.A.D.E.S", font=title_font,
                 fg="#00d4ff", bg="#0d1117").pack()
        tk.Label(header, text="Human AssistANCE and Decision Engine System",
                 font=("Consolas", 8), fg="#4a6fa5", bg="#0d1117").pack()

        # ── Status bar ──────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="● STANDBY")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              font=("Consolas", 9), fg="#00ff88",
                              bg="#0d1117", anchor="w", padx=15)
        status_bar.pack(fill=tk.X)

        # ── Divider ─────────────────────────────────────────────────────────
        tk.Frame(self.root, bg="#00d4ff", height=1).pack(fill=tk.X, padx=10)

        # ── Chat log ────────────────────────────────────────────────────────
        self.chat_log = scrolledtext.ScrolledText(
            self.root, state="disabled",
            bg="#0a0a0f", fg="#c8d6e5",
            font=("Consolas", 11),
            wrap=tk.WORD,
            bd=0, padx=10, pady=10,
            insertbackground="#00d4ff",
            selectbackground="#1a3a5c"
        )
        self.chat_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Configure text tags for colors
        self.chat_log.tag_config("you",    foreground="#00d4ff", font=("Consolas", 11, "bold"))
        self.chat_log.tag_config("hades", foreground="#00ff88", font=("Consolas", 11, "bold"))
        self.chat_log.tag_config("msg",    foreground="#c8d6e5", font=("Consolas", 11))
        self.chat_log.tag_config("time",   foreground="#4a6fa5", font=("Consolas", 9))
        self.chat_log.tag_config("system", foreground="#ff9500", font=("Consolas", 10, "italic"))

        # ── Bottom bar ──────────────────────────────────────────────────────
        tk.Frame(self.root, bg="#00d4ff", height=1).pack(fill=tk.X, padx=10)
        bottom = tk.Frame(self.root, bg="#0d1117", pady=6)
        bottom.pack(fill=tk.X)
        self.bottom_label = tk.Label(bottom, text="Say  'Hades'  to activate",
                                     font=("Consolas", 9), fg="#4a6fa5", bg="#0d1117")
        self.bottom_label.pack()

        self.add_system_message("HADES initialized. All systems nominal.")

    def add_message(self, sender, message):
        self.root.after(0, self._insert_message, sender, message)

    def _insert_message(self, sender, message):
        self.chat_log.config(state="normal")
        now = datetime.datetime.now().strftime("%H:%M")
        if sender == "You":
            self.chat_log.insert(tk.END, f"\n[{now}] ", "time")
            self.chat_log.insert(tk.END, "YOU\n", "you")
        else:
            self.chat_log.insert(tk.END, f"\n[{now}] ", "time")
            self.chat_log.insert(tk.END, "HADES\n", "hades")
        self.chat_log.insert(tk.END, f"{message}\n", "msg")
        self.chat_log.config(state="disabled")
        self.chat_log.see(tk.END)

    def add_system_message(self, message):
        self.root.after(0, self._insert_system, message)

    def _insert_system(self, message):
        self.chat_log.config(state="normal")
        self.chat_log.insert(tk.END, f"⬡ {message}\n", "system")
        self.chat_log.config(state="disabled")
        self.chat_log.see(tk.END)

    def set_status(self, status):
        statuses = {
            "standby":   ("● STANDBY",   "#4a6fa5"),
            "listening": ("◉ LISTENING", "#00ff88"),
            "thinking":  ("◈ THINKING",  "#ff9500"),
            "speaking":  ("◎ SPEAKING",  "#00d4ff"),
        }
        text, color = statuses.get(status, ("● STANDBY", "#4a6fa5"))
        self.root.after(0, lambda: self.status_var.set(text))

    def show(self):
        self.root.after(0, self.root.deiconify)

    def hide(self):
        self.root.after(0, self.root.withdraw)