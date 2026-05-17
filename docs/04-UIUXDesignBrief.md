# Document 04 — UI/UX Design Brief: Visual & Interaction Design Guide

## Aesthetic
Sci-fi command center. Dark, immersive, minimal chrome. Inspired by the HUD displays in Iron Man and the terminal-forward UIs of tools like Vercel and Linear — but with a cinematic, JARVIS-like personality layered on top. Everything should feel like it belongs in a high-tech ops center, not a consumer app.

---

## Color Palette

| Role | Value | Usage |
|---|---|---|
| Background | `#020408` | Full window background |
| Primary cyan | `#00e5ff` | Orb glow, borders, active elements, status text |
| Cyan dim | `#0a4a5a` | Ring borders, scrollbar thumb, inactive text |
| Cyan deep | `#003a4a` | Panel borders, input borders, ring accents |
| Text (primary) | `#cfefff` | All chat text, general content |
| Text (dim) | `#4d7a88` | Timestamps, system messages, placeholder text |
| User message accent | `#ffb64d` | "You:" label in chat — amber/gold to contrast HADES cyan |
| Font background | `rgba(0, 20, 30, 0.3)` | Chat panel and input field fill |

---

## Typography
- **Font family**: `"Courier New", ui-monospace, monospace` — monospace throughout, no exceptions
- **Titlebar**: 10px, letter-spacing 2px, all-caps
- **Status label**: 11px, letter-spacing 4px
- **Chat text**: 13px, line-height 1.55
- **Input field**: 13px
- **Orb label (H.A.D.E.S)**: 18px bold, letter-spacing 5px, glowing text-shadow
- **System messages**: 12px italic, dim color

---

## Component Style
- **Corners**: 4–6px radius on panels and inputs; orb is perfectly circular
- **Borders**: 1px solid `var(--cyan-deep)` on panels; `var(--cyan)` on focused inputs
- **Shadows / Glow**: Orb uses layered `box-shadow` for depth (30px + 70px glow radii); focus states use `box-shadow: 0 0 10px rgba(0,229,255,0.3)`; no heavy drop shadows on panels
- **No gradients on UI panels** — backgrounds are flat semi-transparent fills
- **No icons** — everything is text, borders, and animated geometry

---

## Orb Design
The orb is the visual centrepiece and the status indicator:
- 130px diameter sphere rendered in CSS with `radial-gradient` + `box-shadow` glow
- Surrounded by 4 rotating rings (`r1`–`r4`) at varied sizes, speeds, and directions
- A tick-mark ring (36 ticks at 10° intervals, 4 larger at 90° intervals) rotates slowly
- A grid-dot background inside the stage uses `mask-image` radial gradient to fade at edges
- Orb label "H.A.D.E.S" floats centered on the orb with cyan text-shadow glow

**State animations** (driven by `body[data-status]` CSS selectors):
- `standby`: default slow pulse (3.2s), normal glow
- `listening`: fast pulse (1.2s), bright oversized glow
- `thinking`: `hue-rotate(40deg)` amber shift, rapid pulse (0.8s)
- `speaking`: `hue-rotate(-30deg) saturate(1.4)` blue-white shift, fastest pulse (0.6s), largest glow

---

## Dark / Light Mode
Dark mode only. No light mode variant. The aesthetic depends entirely on dark backgrounds for the glow effects to land correctly.

---

## Reference Apps / Inspirations
- **JARVIS / FRIDAY** (MCU Iron Man) — the gold standard for AI assistant UI personality
- **Vercel dashboard** — minimal, monospace-adjacent, subtle borders
- **Linear** — dense information, no wasted space, fast feel
- **Raycast** — command-center mentality, keyboard-first, instant response

---

## Key UI Patterns

| Pattern | Implementation |
|---|---|
| Chat log | Scrollable `div`, auto-scrolls to bottom on new message |
| Message format | `[timestamp] WHO: message` — three-part structure |
| System messages | Italic, dim, wrapped in em-dashes: `— message —` |
| Status indicator | Text label below orb + CSS class on `body` tag |
| Input bar | Full-width text field + SEND button; Enter key submits |
| Hover states | Buttons glow cyan on hover with `box-shadow` |
| Disabled state | Not implemented — input stays active at all times |

---

## Animation Principles
- All animations are CSS `@keyframes` — no JS animation libraries
- Ring rotations: continuous, no easing (`linear`)
- Orb pulse: `ease-in-out`, scale between 1.0 and 1.06
- State transitions on orb: `transition: all 0.35s ease` for smooth state changes
- No page transitions (single-page app)

---

## Mobile Responsiveness
Not applicable. HADES is a desktop Windows application. The pywebview window has a fixed layout; `overflow: hidden` on body prevents scrolling. No responsive breakpoints needed.

---

## Accessibility
- High contrast: cyan text on near-black background exceeds WCAG AA for large text
- Monospace font aids readability of technical output (stock tickers, code, paths)
- No color-only information — status text always accompanies color/animation changes
- Keyboard accessible: Enter submits input; no mouse required for text-command mode
- Screen reader support: not a priority (voice interface is the primary accessibility mechanism)
