import tkinter as tk
from tkinter import scrolledtext, font
import datetime
import math
import random

class HadesGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("H.A.D.E.S")
        self.root.geometry("520x820")
        self.root.configure(bg="#020408")
        self.root.resizable(False, False)

        # Animation state
        self._anim_phase = 0.0
        self._current_status = "standby"
        self._scan_y = 0

        # ── Top title bar ────────────────────────────────────────────────────
        topbar = tk.Frame(self.root, bg="#020408", pady=8)
        topbar.pack(fill=tk.X)
        tk.Label(topbar, text="[ HUMAN ASSISTANCE AND DECISION ENGINE SYSTEM  v2.1 ]",
                 font=("Courier New", 9), fg="#0a4a5a", bg="#020408").pack()

        # ── Main hologram canvas ─────────────────────────────────────────────
        self.canvas = tk.Canvas(self.root, width=520, height=300,
                                bg="#020408", highlightthickness=0)
        self.canvas.pack()

        cx, cy = 260, 150
        self.cx, self.cy = cx, cy

        # Background grid
        self._draw_grid()

        # Rotating orbit rings (simulate 3D)
        self.orbit_a = self.canvas.create_oval(cx-110, cy-28, cx+110, cy+28,
                                                outline="#003a4a", width=1)
        self.orbit_b = self.canvas.create_oval(cx-28, cy-110, cx+28, cy+110,
                                                outline="#003a4a", width=1)

        # Outer halos
        self.halo3 = self.canvas.create_oval(cx-95, cy-95, cx+95, cy+95,
                                              outline="#001a22", width=3)
        self.halo2 = self.canvas.create_oval(cx-82, cy-82, cx+82, cy+82,
                                              outline="#003344", width=2)
        self.halo1 = self.canvas.create_oval(cx-70, cy-70, cx+70, cy+70,
                                              outline="#005566", width=1)

        # Rotating tick marks
        self.ticks = []
        for i in range(24):
            angle = i * (360 / 24)
            rad = math.radians(angle)
            length = 8 if i % 6 == 0 else (5 if i % 3 == 0 else 3)
            x1 = cx + 72 * math.cos(rad)
            y1 = cy + 72 * math.sin(rad)
            x2 = cx + (72 + length) * math.cos(rad)
            y2 = cy + (72 + length) * math.sin(rad)
            color = "#00aacc" if i % 6 == 0 else "#003344"
            t = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1)
            self.ticks.append(t)

        # Pulse rings
        self.pulse3 = self.canvas.create_oval(cx-68, cy-68, cx+68, cy+68,
                                               outline="#004455", width=1)
        self.pulse2 = self.canvas.create_oval(cx-58, cy-58, cx+58, cy+58,
                                               outline="#006677", width=2)
        self.pulse1 = self.canvas.create_oval(cx-48, cy-48, cx+48, cy+48,
                                               outline="#00aabb", width=2)

        # Core sphere
        self.core_glow = self.canvas.create_oval(cx-38, cy-38, cx+38, cy+38,
                                                  fill="#001a2a", outline="#00cfff", width=2)
        self.core_mid  = self.canvas.create_oval(cx-24, cy-24, cx+24, cy+24,
                                                  fill="#002233", outline="#00ddee", width=1)

        # HADES text dead center
        self.hades_text = self.canvas.create_text(
            cx, cy, text="HADES",
            font=font.Font(family="Courier New", size=13, weight="bold"),
            fill="#00ffee")

        # Scanline
        self.scanline = self.canvas.create_line(0, 0, 520, 0,
                                                 fill="#00cfff", width=1,
                                                 stipple="gray12")

        # HUD corners
        self._draw_hud_corners()

        # Status arc
        self.status_arc = self.canvas.create_arc(
            cx-90, cy-90, cx+90, cy+90,
            start=200, extent=0,
            outline="#00cfff", width=2, style=tk.ARC)

        # Status label
        self.status_text = self.canvas.create_text(
            cx, cy+118, text="◈  STANDBY",
            font=("Courier New", 9), fill="#2a6a7a")

        # ── Divider ──────────────────────────────────────────────────────────
        div = tk.Canvas(self.root, width=520, height=16,
                        bg="#020408", highlightthickness=0)
        div.pack(fill=tk.X)
        div.create_line(20, 8, 500, 8, fill="#003344", width=1)
        div.create_line(20, 8, 80, 8, fill="#00cfff", width=1)
        div.create_line(440, 8, 500, 8, fill="#00cfff", width=1)
        div.create_text(260, 8, text="━━  COMM LOG  ━━",
                        font=("Courier New", 7), fill="#005566")

        # ── Chat log ─────────────────────────────────────────────────────────
        self.chat_log = scrolledtext.ScrolledText(
            self.root, state="disabled",
            bg="#020408", fg="#c8d6e5",
            font=("Courier New", 10),
            wrap=tk.WORD, bd=0, padx=14, pady=10,
            insertbackground="#00cfff",
            selectbackground="#0a2a3a")
        self.chat_log.pack(padx=12, pady=6, fill=tk.BOTH, expand=True)

        self.chat_log.tag_config("you",    foreground="#00cfff",  font=("Courier New", 10, "bold"))
        self.chat_log.tag_config("hades",  foreground="#00ff99",  font=("Courier New", 10, "bold"))
        self.chat_log.tag_config("msg",    foreground="#7a9aaa",  font=("Courier New", 10))
        self.chat_log.tag_config("time",   foreground="#0a2a3a",  font=("Courier New", 8))
        self.chat_log.tag_config("system", foreground="#ff7700",  font=("Courier New", 9, "italic"))

        # ── Bottom bar ───────────────────────────────────────────────────────
        self._bottom_canvas = tk.Canvas(self.root, width=520, height=28,
                                         bg="#020408", highlightthickness=0)
        self._bottom_canvas.pack(fill=tk.X)
        self._bottom_canvas.create_line(20, 6, 500, 6, fill="#003344", width=1)
        self.bottom_text_id = self._bottom_canvas.create_text(
            260, 18, text="say  'hades'  to activate",
            font=("Courier New", 8), fill="#1a4a5a")

        self.add_system_message("HADES initialized. All systems nominal.")
        self._animate()

    def _draw_grid(self):
        cx = 260
        for i in range(7):
            y = 185 + i * 16
            self.canvas.create_line(0, y, 520, y, fill="#001520", width=1)
        for i in range(14):
            x = i * 40
            self.canvas.create_line(x, 300, cx, 148, fill="#001018", width=1)

    def _draw_hud_corners(self):
        s, p, c = 14, 8, "#005566"
        self.canvas.create_line(p, p+s, p, p, p+s, p, fill=c, width=2)
        self.canvas.create_line(520-p-s, p, 520-p, p, 520-p, p+s, fill=c, width=2)
        self.canvas.create_line(p, 300-p-s, p, 300-p, p+s, 300-p, fill=c, width=2)
        self.canvas.create_line(520-p-s, 300-p, 520-p, 300-p, 520-p, 300-p-s, fill=c, width=2)

    def _animate(self):
        self._anim_phase += 0.06
        cx, cy = self.cx, self.cy
        s = self._current_status

        if s == "speaking":
            pulse  = 1.0 + 0.32 * abs(math.sin(self._anim_phase * 2.6))
            corep  = 1.0 + 0.50 * abs(math.sin(self._anim_phase * 2.6))
            rc, cc, gc, dc = "#00ffee", "#00ffee", "#00cfff", "#005566"
            arc_ext = 280
            sl, sc = "◎  SPEAKING", "#00ff99"
            txt_c = "#00ffee" if random.random() > 0.07 else "#007788"

        elif s == "listening":
            pulse  = 1.0 + 0.13 * abs(math.sin(self._anim_phase * 1.5))
            corep  = 1.0 + 0.20 * abs(math.sin(self._anim_phase * 1.5))
            rc, cc, gc, dc = "#00cfff", "#00cfff", "#0088aa", "#003344"
            arc_ext = 180
            sl, sc = "◉  LISTENING", "#00cfff"
            txt_c = "#00cfff"

        elif s == "thinking":
            pulse  = 1.0 + 0.07 * math.sin(self._anim_phase)
            corep  = 1.0 + 0.12 * abs(math.sin(self._anim_phase * 1.3))
            rc, cc, gc, dc = "#ff8800", "#ffaa33", "#884400", "#331100"
            arc_ext = int(90 + 90 * abs(math.sin(self._anim_phase * 0.8)))
            sl, sc = "◈  THINKING", "#ff9500"
            txt_c = "#ffaa33"

        else:
            pulse  = 1.0 + 0.035 * math.sin(self._anim_phase * 0.45)
            corep  = 1.0 + 0.050 * math.sin(self._anim_phase * 0.45)
            rc, cc, gc, dc = "#006677", "#007788", "#003344", "#001a22"
            arc_ext = 45
            sl, sc = "◈  STANDBY", "#2a6a7a"
            txt_c = "#00aabb"

        # Pulse rings
        for ring, base_r, color in [(self.pulse1, 48, rc),
                                     (self.pulse2, 58, gc),
                                     (self.pulse3, 68, dc)]:
            r = base_r * pulse
            self.canvas.coords(ring, cx-r, cy-r, cx+r, cy+r)
            self.canvas.itemconfig(ring, outline=color)

        # Core
        cr = 24 * corep
        self.canvas.coords(self.core_mid, cx-cr, cy-cr, cx+cr, cy+cr)
        self.canvas.itemconfig(self.core_glow, outline=rc)
        self.canvas.itemconfig(self.core_mid,  outline=gc)

        # HADES text flicker
        self.canvas.itemconfig(self.hades_text, fill=txt_c)

        # Orbit rings (3D rotation illusion)
        angle_a = self._anim_phase * 0.7
        ry_a = max(abs(28 * math.sin(angle_a)), 2)
        self.canvas.coords(self.orbit_a, cx-110, cy-ry_a, cx+110, cy+ry_a)
        self.canvas.itemconfig(self.orbit_a, outline=gc)

        angle_b = self._anim_phase * 0.7 + math.pi / 2
        rx_b = max(abs(28 * math.sin(angle_b)), 2)
        self.canvas.coords(self.orbit_b, cx-rx_b, cy-110, cx+rx_b, cy+110)
        self.canvas.itemconfig(self.orbit_b, outline=gc)

        # Scanline sweep
        self._scan_y = (self._scan_y + 2) % 300
        self.canvas.coords(self.scanline, 0, self._scan_y, 520, self._scan_y)
        self.canvas.itemconfig(self.scanline, fill=rc)

        # Status arc
        self.canvas.itemconfig(self.status_arc, outline=rc, extent=arc_ext)

        # Rotating ticks
        offset = self._anim_phase * 0.4
        for i, tick in enumerate(self.ticks):
            rad = math.radians(i * (360/24) + math.degrees(offset))
            length = 8 if i % 6 == 0 else (5 if i % 3 == 0 else 3)
            x1, y1 = cx + 72*math.cos(rad), cy + 72*math.sin(rad)
            x2, y2 = cx + (72+length)*math.cos(rad), cy + (72+length)*math.sin(rad)
            self.canvas.coords(tick, x1, y1, x2, y2)
            self.canvas.itemconfig(tick, fill=rc if i % 6 == 0 else gc)

        # Status label
        self.canvas.itemconfig(self.status_text, text=sl, fill=sc)

        self.root.after(28, self._animate)

    # ── Public API ────────────────────────────────────────────────────────────
    def set_status(self, status):
        self._current_status = status
        labels = {
            "standby":   "say  'hades'  to activate",
            "listening": "■ listening...",
            "thinking":  "■ processing...",
            "speaking":  "■ speaking...",
        }
        self.root.after(0, lambda: self._bottom_canvas.itemconfig(
            self.bottom_text_id, text=labels.get(status, "")))

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

    def show(self):
        self.root.after(0, self.root.deiconify)

    def hide(self):
        self.root.after(0, self.root.withdraw)


if __name__ == "__main__":
    import time, threading
    gui = HadesGUI()
    def demo():
        time.sleep(2)
        for status in ["listening", "thinking", "speaking", "standby"]:
            gui.set_status(status)
            gui.add_message("You" if status == "listening" else "Hades",
                            f"Demo mode: {status}")
            time.sleep(3)
    threading.Thread(target=demo, daemon=True).start()
    gui.root.mainloop()