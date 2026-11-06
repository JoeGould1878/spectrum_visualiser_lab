"""Generate spectrum_visualiser.kicad_sch (KiCad 7 format, opens in KiCad 7/8/9).

Real KiCad parts from the standard libraries (Device:R, Device:C, Device:C_Polarized,
Device:Microphone_Condenser, Amplifier_Operational:LM358, Switch:SW_Push,
Connector_Generic:Conn_01x05, power:*), embedded in the file so it opens on any
machine. ESP32-S3 pins are global labels (no MCU block). Pin positions are read
from the library, so wires land exactly on pins; check with:

    kicad-cli sch erc spectrum_visualiser.kicad_sch
    kicad-cli sch export netlist spectrum_visualiser.kicad_sch

Needs the KiCad symbol library (/usr/share/kicad/symbols, or KICAD7_SYMBOL_DIR).
Written by Claude (Anthropic) for Joe Gould; circuit = the one-stage LM358 build.
"""
import math, os, re, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LIBDIR = os.environ.get("KICAD7_SYMBOL_DIR", "/usr/share/kicad/symbols")
PROJECT = "spectrum_visualiser"
ROOT = str(uuid.uuid5(uuid.NAMESPACE_URL, "spectrum_visualiser/root"))
_n = 0
def uid():
    global _n; _n += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"spectrum_visualiser/{_n}"))

# ---------------------------------------------------------------- library access
def _block(t, start):
    d = 0
    for j in range(start, len(t)):
        if t[j] == "(": d += 1
        elif t[j] == ")":
            d -= 1
            if d == 0: return t[start:j + 1]
_cache = {}
def _custom_lib():
    """Project library 'spectrum': +3V3_MIC = power:+3V3 with its own net name."""
    b = lib_block("power", "+3V3").replace('(symbol "+3V3_', '(symbol "+3V3_MIC_').replace('"+3V3"', '"+3V3_MIC"')
    b = re.sub(r'\(property "ki_description" "(?:[^"\\]|\\.)*"', '(property "ki_description" "Filtered 3.3 V rail for the mic preamp"', b)
    return '(kicad_symbol_lib (version 20220914) (generator gen_kicad_sch)\n  ' + b + '\n)\n'
def lib_block(lib, name):
    if lib == "spectrum" and lib not in _cache:
        _cache[lib] = _custom_lib()
    if lib not in _cache:
        _cache[lib] = open(os.path.join(LIBDIR, lib + ".kicad_sym")).read()
    t = _cache[lib]
    return _block(t, t.index(f'(symbol "{name}"'))

def embedded(lib_id):
    """Flattened symbol block named 'Lib:Name' for lib_symbols."""
    lib, name = lib_id.split(":")
    b = lib_block(lib, name)
    m = re.match(r'\(symbol "[^"]+" \(extends "([^"]+)"\)', b)
    if m:  # derived symbol: base body + this symbol's properties
        base = lib_block(lib, m.group(1))
        props = re.findall(r'\(property .*?\n    \)', b, re.S)
        body = re.sub(r'\(property .*?\n    \)\n\s*', "", base, flags=re.S)
        body = body.replace(f'(symbol "{m.group(1)}_', f'(symbol "{name}_')
        head, rest = body.split("\n", 1)
        head = head.replace(f'(symbol "{m.group(1)}"', f'(symbol "{name}"')
        b = head + "\n    " + "\n    ".join(props) + "\n" + rest
    return b.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)

def lib_pins(lib_id):
    """{(unit, number): (x, y)} in library coordinates (y up). Unit 0 = all units."""
    lib, name = lib_id.split(":")
    b = embedded(lib_id)
    out = {}
    for m in re.finditer(r'\(symbol "%s_(\d+)_(\d+)"' % re.escape(name), b):
        sb = _block(b, m.start())
        for p in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) [-\d.]+\).*?\(number "([^"]+)"', sb, re.S):
            out[(int(m.group(1)), p.group(3))] = (float(p.group(1)), float(p.group(2)))
    return out

# ---------------------------------------------------------------- schematic model
symbols, wires, junctions, labels, texts, rects = [], [], [], [], [], []
used_libs = []
pinpos = {}

def r2(v): return round(v * 100) / 100

def place(lib_id, ref, value, x, y, rot=0, unit=1, props=None, hide_ref=False, mirror=None):
    if lib_id not in used_libs: used_libs.append(lib_id)
    pins = lib_pins(lib_id)
    a = math.radians(rot)
    def tr(px, py):
        xr = px * math.cos(a) - py * math.sin(a)
        yr = px * math.sin(a) + py * math.cos(a)
        return (r2(x + xr), r2(y - yr))
    mine = {num: tr(*xy) for (u, num), xy in pins.items() if u in (0, unit)}
    key = ref if lib_id != "Amplifier_Operational:LM358" else f"{ref}{'ABC'[unit-1]}"
    pinpos[key] = mine
    symbols.append(dict(lib_id=lib_id, ref=ref, value=value, x=x, y=y, rot=rot, unit=unit,
                        props=props or {}, pins=sorted({n for (u, n) in pins if u in (0, unit)}),
                        hide_ref=hide_ref))
    return mine

def P(key, pin): return pinpos[key][str(pin)]

def wire(*pts):
    for a, b in zip(pts, pts[1:]):
        wires.append((a, b))
def junction(pt): junctions.append(pt)
def glabel(name, pt, angle, shape="bidirectional"): labels.append((name, pt, angle, shape))
def text(s, x, y, size=1.27, bold=False, justify="left"): texts.append((s, x, y, size, bold, justify))
def rect(x1, y1, x2, y2): rects.append((x1, y1, x2, y2))

_pwr = [0]
def power(lib_id, value, pt, rot=0):
    _pwr[0] += 1
    ref = ("#FLG" if "FLAG" in lib_id else "#PWR") + f"{_pwr[0]:02d}"
    place(lib_id, ref, value, pt[0], pt[1], rot, hide_ref=True)

# Property placement helpers: absolute position, angle, justify
def vprops(dx=2.54, side="right"):
    j = "left" if side == "right" else "right"; s = 1 if side == "right" else -1
    return lambda sy: {"Reference": (sy["x"] + s * dx, sy["y"] - 1.27, 0, j),
                       "Value": (sy["x"] + s * dx, sy["y"] + 1.27, 0, j)}
def hprops(dy=2.54):
    return lambda sy: {"Reference": (sy["x"], sy["y"] - dy, 0, "center"),
                       "Value": (sy["x"], sy["y"] + dy, 0, "center")}

GRID = 1.27
def g(n): return r2(n * GRID)

# ================================================================= circuit
# --- preamp supply filter
power("power:+3V3", "+3V3", (27.94, 50.8))
place("Device:R", "R0", "220", 35.56, 55.88, rot=90, props=hprops())
place("Device:C_Polarized", "C0", "100u", 45.72, 59.69, props=vprops())
wire((27.94, 50.8), (27.94, 55.88), P("R0", 1))
N_F = (45.72, 55.88)
wire(P("R0", 2), N_F); wire(N_F, (58.42, 55.88)); junction(N_F)
power("spectrum:+3V3_MIC", "+3V3_MIC", (58.42, 55.88))
power("power:PWR_FLAG", "PWR_FLAG", (58.42, 55.88), rot=180)
power("power:GND", "GND", P("C0", 2))
power("power:GND", "GND", (27.94, 68.58)); power("power:PWR_FLAG", "PWR_FLAG", (27.94, 68.58))

# --- microphone + bias
place("Device:R", "R1", "2.2k", 76.2, 50.8, props=vprops())
power("spectrum:+3V3_MIC", "+3V3_MIC", P("R1", 1))
place("Device:Microphone_Condenser", "MK1", "electret", 76.2, 66.04, props=vprops(3.81))
power("power:GND", "GND", P("MK1", 1))
N_A = (76.2, 59.69)
wire(P("R1", 2), N_A); wire(N_A, P("MK1", 2)); junction(N_A)
place("Device:C_Polarized", "C1", "1u", 85.09, 59.69, rot=90, props=hprops(3.81))
wire(N_A, P("C1", 1))
place("Device:R", "R2", "220k", 96.52, 50.8, props=vprops())
power("spectrum:+3V3_MIC", "+3V3_MIC", P("R2", 1))
place("Device:R", "R3", "100k", 96.52, 64.77, props=vprops(side="left"))
power("power:GND", "GND", P("R3", 2))
N_B = (96.52, 59.69)
wire(P("R2", 2), N_B); wire(N_B, P("R3", 1)); wire(P("C1", 2), N_B); junction(N_B)

# --- U1A: non-inverting, gain 1 + R4/R5
opp = lambda sy: {"Reference": (sy["x"] + 1.27, sy["y"] - 6.35, 0, "left"),
                  "Value": (sy["x"] + 1.27, sy["y"] - 4.445, 0, "left")}
place("Amplifier_Operational:LM358", "U1", "LM358", 114.3, 62.23, unit=1, props=opp)
wire(N_B, P("U1A", 3))
place("Device:R", "R5", "1k", 104.14, 76.2, props=vprops(side="left"))
N_C = P("R5", 1)
wire(P("U1A", 2), (104.14, P("U1A", 2)[1]), N_C)
place("Device:R", "R4", "100k", 114.3, 72.39, rot=90, props=hprops())
wire(N_C, P("R4", 1)); junction(N_C)
N_D = (124.46, 62.23)
wire(P("R4", 2), (124.46, 72.39), N_D); wire(P("U1A", 1), N_D); junction(N_D)
place("Device:C_Polarized", "C2", "10u", 104.14, 85.09, props=vprops(side="left"))
wire(P("R5", 2), P("C2", 1))
power("power:GND", "GND", P("C2", 2))

# --- output: R6 + C4 anti-alias -> GPIO1
place("Device:R", "R6", "4.7k", 132.08, 62.23, rot=90, props=hprops())
wire(N_D, P("R6", 1))
place("Device:C", "C4", "2.2n", 139.7, 66.04, props=vprops())
N_E = P("C4", 1)
wire(P("R6", 2), N_E); wire(N_E, (147.32, 62.23)); junction(N_E)
power("power:GND", "GND", P("C4", 2))
glabel("GPIO1", (147.32, 62.23), 0, "output")

# --- U1B unused: + to GND, output to -
place("Amplifier_Operational:LM358", "U1", "LM358", 127.0, 91.44, unit=2, props=opp)
wire(P("U1B", 5), (111.76, 88.9)); power("power:GND", "GND", (111.76, 88.9))
wire(P("U1B", 6), (116.84, 93.98), (116.84, 99.06), (137.16, 99.06), (137.16, 91.44), P("U1B", 7))

# --- U1C power + decoupling
place("Amplifier_Operational:LM358", "U1", "LM358", 152.4, 88.9, unit=3,
      props=lambda sy: {"Reference": (sy["x"] + 1.27, sy["y"] - 1.27, 0, "left"),
                        "Value": (sy["x"] + 1.27, sy["y"] + 1.27, 0, "left")})
power("spectrum:+3V3_MIC", "+3V3_MIC", P("U1C", 8)); power("power:GND", "GND", P("U1C", 4))
place("Device:C", "C5", "100n", 142.24, 88.9, props=vprops(side="left"))
power("spectrum:+3V3_MIC", "+3V3_MIC", P("C5", 1)); power("power:GND", "GND", P("C5", 2))

# --- LED matrix module header
place("Connector_Generic:Conn_01x05", "J1", "MAX7219_4in1", 220.98, 58.42,
      props=lambda sy: {"Reference": (sy["x"], sy["y"] - 8.89, 0, "center"),
                        "Value": (sy["x"], sy["y"] + 8.89, 0, "center")})
wire(P("J1", 1), (208.28, 53.34)); power("power:+5V", "+5V", (208.28, 53.34))
wire(P("J1", 2), (210.82, 55.88)); power("power:GND", "GND", (210.82, 55.88), rot=270)
for pin, net in [(3, "GPIO11"), (4, "GPIO10"), (5, "GPIO12")]:
    pt = P("J1", pin); wire(pt, (198.12, pt[1])); glabel(net, (198.12, pt[1]), 180, "input")
for pin, nm in [(1, "VCC"), (2, "GND"), (3, "DIN"), (4, "CS"), (5, "CLK")]:
    text(nm, 223.52, P("J1", pin)[1] + 0.4, 1.0)

# --- buttons
for ref, val, net, y in [("SW1", "MODE", "GPIO14", 91.44), ("SW2", "LISTEN", "GPIO21", 104.14)]:
    place("Switch:SW_Push", ref, val, 215.9, y,
          props=lambda sy: {"Reference": (sy["x"], sy["y"] - 3.81, 0, "center"),
                            "Value": (sy["x"], sy["y"] + 2.54, 0, "center")})
    wire((203.2, y), P(ref, 1)); glabel(net, (203.2, y), 180, "input")
    wire(P(ref, 2), (226.06, y)); power("power:GND", "GND", (226.06, y))

# ================================================================= annotation
rect(17.78, 33.02, 64.77, 80.01); text("Preamp supply filter", 19.05, 36.83, 1.5, True)
text("Board 3V3 -> R0/C0 -> +3V3_MIC (preamp only).", 19.05, 77.47, 1.1)
rect(67.31, 33.02, 167.64, 120.65); text("Microphone preamp - LM358 (U1), one stage, gain ~x101", 68.58, 36.83, 1.5, True)
text("Gain = 1 + R4/R5 = 101 (40 dB); C2 makes the DC gain 1.", 68.58, 110.49, 1.1)
text("Bias = +3V3_MIC x R3/(R2+R3) = 0.95 V.  R6 + C4: low-pass ~15 kHz.", 68.58, 113.03, 1.1)
text("On 3.3 V the LM358 output stays below ~1.8 V, so GPIO1 is safe.", 68.58, 115.57, 1.1)
text("U1B unused: tied off", 119.38, 102.87, 1.1)
rect(185.42, 33.02, 241.3, 78.74); text("LED matrix - 4 x MAX7219, 32 x 8", 186.69, 36.83, 1.5, True)
text("U3-U6 (MAX7219 + 8x8 LEDs) are on the module.", 186.69, 71.12, 1.1)
text("Known limitation: its ~600 Hz row scan couples into", 186.69, 73.66, 1.1)
text("the preamp through GND; run at brightness 0.", 186.69, 76.2, 1.1)
rect(185.42, 81.28, 241.3, 113.03); text("Buttons", 186.69, 85.09, 1.5, True)
text("ESP32-S3 internal pull-ups; pressed = low.", 186.69, 110.49, 1.1)
rect(17.78, 83.82, 64.77, 152.4); text("ESP32-S3 (U2) pin use", 19.05, 87.63, 1.5, True)
rows = [("Net", "U2 pin", "Goes to"), ("+3V3", "3V3", "R0"), ("+5V", "5V (USB)", "J1 VCC"),
        ("GND", "GND x2", "preamp, J1"), ("GPIO1", "GPIO1 ADC1_CH0", "preamp out"),
        ("GPIO11", "GPIO11 SPI2 MOSI", "J1 DIN"), ("GPIO12", "GPIO12 SPI2 SCLK", "J1 CLK"),
        ("GPIO10", "GPIO10 CS", "J1 CS"), ("GPIO14", "GPIO14 pull-up", "SW1 MODE"),
        ("GPIO21", "GPIO21 pull-up", "SW2 LISTEN")]
for i, r in enumerate(rows):
    yy = 92.71 + i * 4.445
    for x, s in zip((19.05, 31.75, 48.26), r): text(s, x, yy, 1.1, i == 0)
text("Global labels on this sheet = U2 pins.", 19.05, 140.97, 1.1)
text("Camera ribbon unplugged (Freenove board).", 19.05, 143.51, 1.1)
rect(67.31, 124.46, 167.64, 152.4); text("Notes", 68.58, 128.27, 1.5, True)
for i, s in enumerate(["1. All GND symbols are one net. Return the preamp GND and J1 GND to different U2 GND pins.",
                       "2. Electrolytics: C0 + to +3V3_MIC, C1 + to MK1, C2 + to R5. MK1 - is the pin joined to its case.",
                       "3. DC check before wiring GPIO1: U1 pin 3 ~0.95 V, pin 1 ~0.9-1.1 V (quiet room).",
                       "4. Two-stage option (x1100): U1B becomes a x11 stage, see docs/diagrams/preamp-2.png.",
                       "5. +3V3_MIC is its own power net (project library spectrum.kicad_sym), not the board 3V3."]):
    text(s, 68.58, 132.08 + i * 3.81, 1.1)

# ================================================================= write
def eff(size=1.27, bold=False, justify=None, hide=False):
    s = f'(effects (font (size {size} {size}){" bold" if bold else ""})'
    if justify and justify != "center": s += f" (justify {justify})"
    if hide: s += " hide"
    return s + ")"

out = []
A = out.append
A(f'(kicad_sch (version 20230121) (generator eeschema)\n  (uuid {ROOT})\n  (paper "A4")\n')
A('  (title_block\n    (title "Spectrum visualiser - full schematic")\n    (date "2026-11-06")\n    (rev "1")\n'
  '    (company "Mini-Challenge 2 (CDIO) - Joe Gould")\n    (comment 1 "One-stage LM358 preamp, ESP32-S3 pins as global labels")\n'
  '    (comment 2 "Generated by hardware/kicad/gen_kicad_sch.py (Claude, Anthropic)")\n  )\n')
A("  (lib_symbols\n")
for lid in used_libs:
    A("    " + embedded(lid).replace("\n", "\n  ") + "\n")
A("  )\n")
for (x, y) in junctions:
    A(f'  (junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid {uid()}))\n')
for (a, b) in wires:
    A(f'  (wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid {uid()}))\n')
for (x1, y1, x2, y2) in rects:
    A(f'  (rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0) (type dash)) (fill (type none)) (uuid {uid()}))\n')
for (s, x, y, size, bold, j) in texts:
    A(f'  (text "{s}" (at {x} {y} 0) {eff(size, bold, j)} (uuid {uid()}))\n')
for (name, (x, y), ang, shape) in labels:
    j = "left" if ang == 0 else "right"
    A(f'  (global_label "{name}" (shape {shape}) (at {x} {y} {ang}) (fields_autoplaced) {eff(justify=j)} (uuid {uid()})\n'
      f'    (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} 0) {eff(justify=j, hide=True)})\n  )\n')
for s in symbols:
    is_pwr = s["lib_id"].startswith(("power:", "spectrum:+3V3"))
    A(f'  (symbol (lib_id "{s["lib_id"]}") (at {s["x"]} {s["y"]} {s["rot"]}) (unit {s["unit"]})\n'
      f'    (in_bom {"no" if is_pwr else "yes"}) (on_board {"no" if is_pwr else "yes"}) (dnp no) (uuid {uid()})\n')
    pp = s["props"](s) if callable(s["props"]) else {}
    if is_pwr:
        up = s["rot"] in (0,) and "FLAG" not in s["lib_id"] and "GND" not in s["lib_id"]
        if "GND" in s["lib_id"]:
            vpos = (s["x"], s["y"] + 3.81) if s["rot"] == 0 else (s["x"] - 5.08, s["y"] + 0.4)
        elif "FLAG" in s["lib_id"]:
            vpos = (s["x"], s["y"] - 3.81) if s["rot"] == 0 else (s["x"], s["y"] + 3.81)
        else:
            vpos = (s["x"], s["y"] - 3.81)
        pp = {"Reference": (s["x"], s["y"] + 6.35, 0, "center"), "Value": (vpos[0], vpos[1], 0, "center")}
    for k in ("Reference", "Value"):
        x, y, ang, j = pp.get(k, (s["x"], s["y"], 0, "center"))
        if not is_pwr and s["rot"] == 90: ang = 90
        val = s["ref"] if k == "Reference" else s["value"]
        hide = (k == "Reference" and s["hide_ref"])
        A(f'    (property "{k}" "{val}" (at {r2(x)} {r2(y)} {ang}) {eff(justify=j, hide=hide)})\n')
    A(f'    (property "Footprint" "" (at {s["x"]} {s["y"]} 0) {eff(hide=True)})\n')
    A(f'    (property "Datasheet" "~" (at {s["x"]} {s["y"]} 0) {eff(hide=True)})\n')
    for n in s["pins"]:
        A(f'    (pin "{n}" (uuid {uid()}))\n')
    A(f'    (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{s["ref"]}") (unit {s["unit"]}))))\n  )\n')
A(f'  (sheet_instances (path "/" (page "1")))\n)\n')

with open(os.path.join(HERE, f"{PROJECT}.kicad_sch"), "w") as f:
    f.write("".join(out))
with open(os.path.join(HERE, "spectrum.kicad_sym"), "w") as f:
    f.write(_custom_lib())
with open(os.path.join(HERE, "sym-lib-table"), "w") as f:
    f.write('(sym_lib_table\n  (version 7)\n  (lib (name "spectrum")(type "KiCad")(uri "${KIPRJMOD}/spectrum.kicad_sym")(options "")(descr "Project symbols"))\n)\n')
pro = os.path.join(HERE, f"{PROJECT}.kicad_pro")
if not os.path.exists(pro):
    with open(pro, "w") as f:
        f.write('{\n  "meta": {\n    "filename": "%s.kicad_pro",\n    "version": 1\n  }\n}\n' % PROJECT)
print("wrote", f"{PROJECT}.kicad_sch", len(symbols), "symbols,", len(wires), "wires")
