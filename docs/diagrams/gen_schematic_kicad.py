"""KiCad-style schematic of the whole build (one-stage LM358 preamp).

Drawn to look like a KiCad Eeschema sheet: power symbols instead of rails,
global labels for the ESP32-S3 pins (no big MCU rectangle), reference +
value on every part, junction dots, page frame and title block.
It is a drawing, not a KiCad project file.

    python3 gen_schematic_kicad.py   ->  schematic-kicad.svg  (render to PNG with Playwright)
"""
from html import escape
import os

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 1600, 900

WIRE, BODY, FILL, PIN, REF, NOTE, LBL = "#008400", "#840000", "#FFFFC2", "#840000", "#006464", "#0000C2", "#000000"
FONT = "'DejaVu Sans','IBM Plex Sans',Arial,sans-serif"

o = []
def add(s): o.append(s)
def text(x, y, s, size=12, color=REF, anchor="start", weight="normal", rot=None):
    r = f' transform="rotate({rot} {x} {y})"' if rot else ""
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}"{a}{r}>{escape(s)}</text>')
def line(x1, y1, x2, y2, color=WIRE, w=1.6):
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')
def wire(*pts):
    d = "M" + "L".join(f"{x} {y}" for x, y in pts)
    add(f'<path d="{d}" fill="none" stroke="{WIRE}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>')
def junction(x, y): add(f'<circle cx="{x}" cy="{y}" r="3.2" fill="{WIRE}"/>')

# ---- symbols (connection points are the outer pin ends)
def R_v(x, y, ref, val, side="right"):        # pins (x, y-30) (x, y+30)
    line(x, y - 30, x, y - 18, PIN); line(x, y + 18, x, y + 30, PIN)
    add(f'<rect x="{x-6}" y="{y-18}" width="12" height="36" fill="{FILL}" stroke="{BODY}" stroke-width="1.4"/>')
    if side == "right": text(x + 12, y - 2, ref); text(x + 12, y + 13, val)
    else: text(x - 12, y - 2, ref, anchor="end"); text(x - 12, y + 13, val, anchor="end")
def R_h(x, y, ref, val):        # pins (x-30, y) (x+30, y)
    line(x - 30, y, x - 18, y, PIN); line(x + 18, y, x + 30, y, PIN)
    add(f'<rect x="{x-18}" y="{y-6}" width="36" height="12" fill="{FILL}" stroke="{BODY}" stroke-width="1.4"/>')
    text(x, y - 12, ref, anchor="middle"); text(x, y + 22, val, anchor="middle")
def C_v(x, y, ref, val, pol=False, side="right"):   # pins (x, y-20) (x, y+20)
    line(x, y - 20, x, y - 4, PIN); line(x, y + 4, x, y + 20, PIN)
    if pol:
        add(f'<rect x="{x-11}" y="{y-6}" width="22" height="3.5" fill="none" stroke="{BODY}" stroke-width="1.4"/>')
        add(f'<rect x="{x-11}" y="{y+2.5}" width="22" height="3.5" fill="{BODY}"/>')
        text(x - 18, y - 6, "+", 11, BODY, "middle")
    else:
        line(x - 11, y - 4, x + 11, y - 4, BODY, 2.2); line(x - 11, y + 4, x + 11, y + 4, BODY, 2.2)
    if side == "right": text(x + 16, y - 2, ref); text(x + 16, y + 13, val)
    else: text(x - 16, y - 2, ref, anchor="end"); text(x - 16, y + 13, val, anchor="end")
def C_h(x, y, ref, val, pol=False):  # pins (x-20, y) (x+20, y); + on the left
    line(x - 20, y, x - 4, y, PIN); line(x + 4, y, x + 20, y, PIN)
    if pol:
        add(f'<rect x="{x-6}" y="{y-11}" width="3.5" height="22" fill="none" stroke="{BODY}" stroke-width="1.4"/>')
        add(f'<rect x="{x+2.5}" y="{y-11}" width="3.5" height="22" fill="{BODY}"/>')
        text(x - 12, y - 12, "+", 11, BODY, "middle")
    else:
        line(x - 4, y - 11, x - 4, y + 11, BODY, 2.2); line(x + 4, y - 11, x + 4, y + 11, BODY, 2.2)
    text(x, y - 18, ref, anchor="middle"); text(x, y + 28, val, anchor="middle")
def GND(x, y, dirn="down"):
    if dirn == "down":
        line(x, y, x, y + 10, BODY, 1.4)
        add(f'<polygon points="{x-9},{y+10} {x+9},{y+10} {x},{y+19}" fill="none" stroke="{BODY}" stroke-width="1.4"/>')
        text(x, y + 32, "GND", 10, BODY, "middle")
    else:  # left
        line(x, y, x - 10, y, BODY, 1.4)
        add(f'<polygon points="{x-10},{y-9} {x-10},{y+9} {x-19},{y}" fill="none" stroke="{BODY}" stroke-width="1.4"/>')
        text(x - 24, y + 4, "GND", 10, BODY, "end")
def PWR(x, y, name):            # connection at (x, y), symbol points up
    line(x, y, x, y - 12, BODY, 1.4)
    add(f'<polyline points="{x-7},{y-7} {x},{y-15} {x+7},{y-7}" fill="none" stroke="{BODY}" stroke-width="1.4"/>')
    text(x, y - 21, name, 10.5, BODY, "middle")
def GLABEL(x, y, name, side="right"):  # pointed end touches the wire at (x, y)
    w = 9 + 7.3 * len(name)
    if side == "right":
        pts = f"{x},{y} {x+9},{y-9} {x+9+w},{y-9} {x+9+w},{y+9} {x+9},{y+9}"; tx = x + 13
        add(f'<polygon points="{pts}" fill="#FFFFFF" stroke="{BODY}" stroke-width="1.2"/>')
        text(tx, y + 4.5, name, 12, LBL)
    else:
        pts = f"{x},{y} {x-9},{y-9} {x-9-w},{y-9} {x-9-w},{y+9} {x-9},{y+9}"; tx = x - 13
        add(f'<polygon points="{pts}" fill="#FFFFFF" stroke="{BODY}" stroke-width="1.2"/>')
        text(tx, y + 4.5, name, 12, LBL, "end")
def pinno(x, y, n): text(x, y, str(n), 9.5, "#A90000", "middle")
def opamp(xl, ytop, ref, val, pins, ref_pos=None):
    """Body: left edge xl, height 120, tip at xl+100. Pins: + at ytop+30, − at ytop+90, out at ytop+60.
    Pin ends: (xl-20, ytop+30), (xl-20, ytop+90), (xl+120, ytop+60)."""
    p, n, out = pins
    add(f'<polygon points="{xl},{ytop} {xl},{ytop+120} {xl+100},{ytop+60}" fill="{FILL}" stroke="{BODY}" stroke-width="1.4"/>')
    line(xl - 20, ytop + 30, xl, ytop + 30, PIN); line(xl - 20, ytop + 90, xl, ytop + 90, PIN)
    line(xl + 100, ytop + 60, xl + 120, ytop + 60, PIN)
    pinno(xl - 10, ytop + 25, p); pinno(xl - 10, ytop + 85, n); pinno(xl + 110, ytop + 55, out)
    text(xl + 6, ytop + 35, "+", 14, BODY); text(xl + 6, ytop + 96, "−", 14, BODY)
    rx, ry = ref_pos or (xl + 40, ytop - 6)
    text(rx, ry, ref); text(rx, ry + 14 if ref_pos else ytop + 138, val)
def mic(x, y, ref, val):        # pins (x, y-30) top (+), (x, y+30) bottom
    line(x, y - 30, x, y - 16, PIN); line(x, y + 16, x, y + 30, PIN)
    add(f'<circle cx="{x}" cy="{y}" r="16" fill="{FILL}" stroke="{BODY}" stroke-width="1.4"/>')
    line(x - 16, y - 16, x - 16, y + 16, BODY, 2.2)
    text(x + 8, y - 20, "+", 11, BODY)
    text(x + 22, y - 2, ref); text(x + 22, y + 13, val)
def sw_push(x, y, ref, val):    # pins (x-30, y) (x+30, y)
    line(x - 30, y, x - 18, y, PIN); line(x + 18, y, x + 30, y, PIN)
    for cx in (x - 15, x + 15): add(f'<circle cx="{cx}" cy="{y}" r="3" fill="#FFFFFF" stroke="{BODY}" stroke-width="1.4"/>')
    line(x - 20, y - 10, x + 20, y - 10, BODY, 1.6); line(x, y - 10, x, y - 20, BODY, 1.6); line(x - 7, y - 20, x + 7, y - 20, BODY, 1.6)
    text(x, y - 28, ref, anchor="middle"); text(x, y + 22, val, anchor="middle")
def section(x, y, w, h, title):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{NOTE}" stroke-width="1" stroke-dasharray="7 4"/>')
    text(x + 10, y + 20, title, 13, NOTE, weight="bold")
def notes(x, y, lines_, size=11.5, dy=17):
    for i, s in enumerate(lines_): text(x, y + i * dy, s, size, NOTE)

# ---------------------------------------------------------------- page frame
add(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>')
add(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" fill="none" stroke="{BODY}" stroke-width="1"/>')
add(f'<rect x="30" y="30" width="{W-60}" height="{H-60}" fill="none" stroke="{BODY}" stroke-width="1"/>')
for i in range(6):
    xz = 30 + (W - 60) * (i + 0.5) / 6
    text(xz, 24, str(i + 1), 11, BODY, "middle"); text(xz, H - 15, str(i + 1), 11, BODY, "middle")
    if i: line(30 + (W - 60) * i / 6, 10, 30 + (W - 60) * i / 6, 30, BODY, 1); line(30 + (W - 60) * i / 6, H - 30, 30 + (W - 60) * i / 6, H - 10, BODY, 1)
for i, ch in enumerate("ABCD"):
    yz = 30 + (H - 60) * (i + 0.5) / 4
    text(20, yz + 4, ch, 11, BODY, "middle"); text(W - 20, yz + 4, ch, 11, BODY, "middle")
    if i: line(10, 30 + (H - 60) * i / 4, 30, 30 + (H - 60) * i / 4, BODY, 1); line(W - 30, 30 + (H - 60) * i / 4, W - 10, 30 + (H - 60) * i / 4, BODY, 1)

# ---------------------------------------------------------------- power filter
section(50, 50, 380, 262, "Preamp supply filter")
PWR(110, 170, "+3V3")
wire((110, 170), (110, 200), (140, 200)); R_h(170, 200, "R0", "220")
wire((200, 200), (340, 200)); junction(260, 200)
wire((260, 200), (260, 230)); C_v(260, 250, "C0", "100µ", pol=True); GND(260, 270)
PWR(340, 200, "+3V3_MIC")
notes(66, 92, ["Board 3V3 → R0/C0 → +3V3_MIC.", "Feeds the preamp only, keeps", "digital noise off the mic."])

# ---------------------------------------------------------------- ESP32 pin map
section(50, 330, 380, 360, "ESP32-S3 (U2) pin use")
rows = [("Net", "U2 pin", "Goes to"), ("+3V3", "3V3", "R0 (preamp supply)"), ("+5V", "5V (USB)", "J1 VCC"),
        ("GND", "GND ×2", "preamp, J1 (2 pins)"), ("GPIO1", "GPIO1 · ADC1_CH0", "preamp out"),
        ("GPIO11", "GPIO11 · SPI2 MOSI", "J1 DIN"), ("GPIO12", "GPIO12 · SPI2 SCLK", "J1 CLK"),
        ("GPIO10", "GPIO10 · CS", "J1 CS"), ("GPIO14", "GPIO14 · pull-up", "SW1 MODE"),
        ("GPIO21", "GPIO21 · pull-up", "SW2 LISTEN")]
tx, ty, rh = 64, 366, 27.5
cols = [64, 140, 294]
for i, r in enumerate(rows):
    yy = ty + i * rh
    for c, s in zip(cols, r):
        text(c, yy + 18, s, 11.5 if i else 11.5, NOTE if i else NOTE, weight="bold" if i == 0 else "normal")
    line(tx - 4, yy + 26, 418, yy + 26, NOTE, 0.6)
notes(64, 650, ["Global labels on this sheet are U2 pins.", "Freenove board: camera ribbon unplugged."])

# ---------------------------------------------------------------- preamp
section(450, 50, 690, 640, "Microphone preamp · LM358 (U1), one stage, gain ≈ ×101")
PWR(520, 170, "+3V3_MIC"); R_v(520, 200, "R1", "2.2k")
wire((520, 230), (520, 280)); junction(520, 260)
mic(520, 310, "MK1", "electret"); GND(520, 340)
wire((520, 260), (570, 260)); C_h(590, 260, "C1", "1µ", pol=True)
wire((610, 260), (710, 260)); junction(660, 260)
PWR(660, 170, "+3V3_MIC"); R_v(660, 200, "R2", "220k"); wire((660, 230), (660, 260))
wire((660, 260), (660, 290)); R_v(660, 320, "R3", "100k", side="left"); GND(660, 350)
opamp(730, 230, "U1A", "LM358", (3, 2, 1), ref_pos=(770, 218))
wire((710, 320), (690, 320), (690, 430)); junction(690, 420)
R_v(690, 460, "R5", "1k")
wire((690, 490), (690, 510)); C_v(690, 530, "C2", "10µ", pol=True); GND(690, 550)
wire((690, 420), (760, 420)); R_h(790, 420, "R4", "100k")
wire((820, 420), (880, 420), (880, 290)); wire((850, 290), (910, 290)); junction(880, 290)
R_h(940, 290, "R6", "4.7k")
wire((970, 290), (1050, 290)); junction(1010, 290)
wire((1010, 290), (1010, 320)); C_v(1010, 340, "C4", "2.2n"); GND(1010, 360)
GLABEL(1050, 290, "GPIO1")
# U1B: unused half, tied off
opamp(900, 480, "U1B", "LM358", (5, 6, 7), ref_pos=(940, 468))
wire((880, 510), (850, 510)); GND(850, 510)
wire((880, 570), (865, 570), (865, 625), (1040, 625), (1040, 540), (1020, 540))
# U1C: power unit
PWR(1080, 396, "+3V3_MIC"); wire((1080, 396), (1080, 410))
line(1080, 410, 1080, 425, PIN); line(1080, 475, 1080, 490, PIN)
add(f'<rect x="1068" y="425" width="24" height="50" fill="{FILL}" stroke="{BODY}" stroke-width="1.4"/>')
text(1080, 441, "V+", 9, REF, "middle"); text(1080, 470, "V−", 9, REF, "middle")
pinno(1088, 421, 8); pinno(1088, 486, 4)
text(1097, 447, "U1C"); text(1097, 461, "LM358")
GND(1080, 490)
wire((1040, 412), (1040, 396), (1080, 396)); junction(1080, 396)
C_v(1040, 432, "C5", "100n", side="left"); GND(1040, 452)
notes(466, 652, ["Gain = 1 + R4/R5 ≈ 101 (40 dB); C2 makes the DC gain 1.   Bias = +3V3_MIC × R3/(R2+R3) ≈ 0.95 V.",
                 "R6 + C4: anti-alias low-pass ≈ 15 kHz.   On 3.3 V the LM358 output stays ≤ 1.8 V, so GPIO1 is safe."])
text(900, 612, "U1B unused: tied off", 10.5, NOTE)

# ---------------------------------------------------------------- LED matrix
section(1160, 50, 390, 420, "LED matrix · 4 × MAX7219, 32 × 8")
jx, jy0 = 1440, 150
add(f'<rect x="{jx}" y="{jy0}" width="64" height="150" fill="{FILL}" stroke="{BODY}" stroke-width="1.4"/>')
names = ["VCC", "GND", "DIN", "CS", "CLK"]
for i, nm in enumerate(names):
    yy = jy0 + 15 + i * 30
    line(jx - 20, yy, jx, yy, PIN); pinno(jx - 10, yy - 5, i + 1); text(jx + 6, yy + 4, nm, 11, REF)
text(jx + 32, jy0 - 8, "J1", anchor="middle"); text(jx + 32, jy0 + 168, "MAX7219 module, input", anchor="middle")
wire((jx - 20, 165), (1370, 165)); PWR(1370, 165, "+5V")
wire((jx - 20, 195), (1395, 195)); GND(1395, 195, "left")
for yy, nm in [(225, "GPIO11"), (255, "GPIO10"), (285, "GPIO12")]:
    wire((jx - 20, yy), (1300, yy)); GLABEL(1300, yy, nm, side="left")
notes(1176, 352, ["U3–U6 (MAX7219 + 8×8 LEDs) are on the module,",
                  "chained DOUT → DIN. Runs at 5 V; 3.3 V logic in",
                  "is below the 3.5 V spec (watch for stray pixels).",
                  "Known limitation: its ≈ 600 Hz row scan couples",
                  "into the preamp through GND; run at brightness 0."])

# ---------------------------------------------------------------- buttons
section(1160, 490, 390, 200, "Buttons")
for y, ref, val, net in [(555, "SW1", "MODE", "GPIO14"), (630, "SW2", "LISTEN", "GPIO21")]:
    wire((1310, y), (1370, y)); GLABEL(1310, y, net, side="left")
    sw_push(1400, y, ref, val)
    wire((1430, y), (1470, y)); GND(1470, y)
notes(1176, 676, ["U2 internal pull-ups; pressed = low."], 11)

# ---------------------------------------------------------------- general notes
section(50, 710, 970, 150, "Notes")
notes(66, 750, ["1. All GND symbols are one net. Return the preamp GND and J1 GND to different U2 GND pins.",
                "2. Electrolytics: C0 + to +3V3_MIC, C1 + to MK1, C2 + to R5.  MK1 − is the pin joined to its case.",
                "3. DC check before wiring GPIO1: U1 pin 3 ≈ 0.95 V, pin 1 ≈ 0.9–1.1 V (quiet room).",
                "4. Two-stage option (×1100): U1B becomes a ×11 stage — see preamp-2.png.",
                "5. Drawn in KiCad style for the report; not a KiCad project file."], 12, 20)

# ---------------------------------------------------------------- title block
bx, by, bw, bh = 1040, 750, 530, 120
add(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="#FFFFFF" stroke="{BODY}" stroke-width="1.2"/>')
for yy in (by + 26, by + 52, by + 90): line(bx, yy, bx + bw, yy, BODY, 1)
line(bx + 300, by + 52, bx + 300, by + 90, BODY, 1)
text(bx + 8, by + 18, "Spectrum visualiser · Mini-Challenge 2 (CDIO) · ESP32-S3", 11, BODY)
text(bx + 8, by + 45, "Title: Full schematic, one-stage LM358 preamp", 13, LBL, weight="bold")
text(bx + 8, by + 76, "Drawn: Joe Gould, with Claude (Anthropic)", 11, BODY)
text(bx + 308, by + 76, "Date: 2026-11-06     Rev: 1", 11, BODY)
text(bx + 8, by + 110, "Size: A4    Sheet: 1/1    Source: docs/diagrams/gen_schematic_kicad.py", 10.5, BODY)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
       f'font-family="{FONT}">' + "".join(o) + "</svg>")
with open(os.path.join(OUT, "schematic-kicad.svg"), "w") as f:
    f.write(svg)
print("ok")
