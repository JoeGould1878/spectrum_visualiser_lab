"""Generate the spectrum visualiser system diagrams.

One source for both outputs:
  - the themed web page (diagrams.html, colours from CSS tokens)
  - standalone light SVGs for the report (svg/*.svg), later rendered to PNG

All coordinates are hand-placed on a 1000/1040-wide canvas.
"""
from html import escape
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- helpers
def esc(s):
    return escape(s, quote=True)

def T(x, y, s, cls="t", anchor="start"):
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    return f'<text x="{x}" y="{y}" class="{cls}"{a}>{esc(s)}</text>'

def R(x, y, w, h, cls="bx", rx=6):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="{cls}"/>'

def P(d, cls="w", arrow=None):
    m = f' marker-end="url(#ar-{arrow})"' if arrow else ""
    return f'<path d="{d}" class="{cls}"{m}/>'

def L(x1, y1, x2, y2, cls="w", arrow=None):
    return P(f"M{x1} {y1}L{x2} {y2}", cls, arrow)

def dot(x, y, r=3.2):
    return f'<circle cx="{x}" cy="{y}" r="{r}" class="dot"/>'

def gnd(x, y):
    """Ground symbol hanging from (x, y)."""
    return (L(x, y, x, y + 8, "w w-gnd") +
            L(x - 10, y + 8, x + 10, y + 8, "w w-gnd") +
            L(x - 6, y + 12, x + 6, y + 12, "w w-gnd") +
            L(x - 2, y + 16, x + 2, y + 16, "w w-gnd"))

def box(x, y, w, h, title, lines=(), cls="bx", tcls="tb", lcls="ts", center=False, pad=14, title_dy=22, line_h=17):
    out = [R(x, y, w, h, cls)]
    if center:
        cx = x + w / 2
        out.append(T(cx, y + title_dy, title, tcls, "middle"))
        for i, s in enumerate(lines):
            out.append(T(cx, y + title_dy + line_h * (i + 1), s, lcls, "middle"))
    else:
        out.append(T(x + pad, y + title_dy, title, tcls))
        for i, s in enumerate(lines):
            out.append(T(x + pad, y + title_dy + line_h * (i + 1), s, lcls))
    return "".join(out)

DEFS = """<defs>
<marker id="ar-ink" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="mk"/></marker>
<marker id="ar-sig" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="mk-sig"/></marker>
<marker id="ar-spi" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="mk-spi"/></marker>
</defs>"""

CROP = 48

def svg(w, h, label, body):
    return (w, h, label, body)

def page_svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {CROP} {w} {h - CROP}" role="img" '
            f'aria-label="{esc(label)}">{DEFS}{body}</svg>')

def report_svg(w, h, label, body, style, bg):
    title = f'<text x="24" y="34" class="th">{esc(label)}</text>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{esc(label)}">{DEFS}<style>{style}</style><rect width="100%" height="100%" fill="{bg}"/>'
            f'{title}{body}</svg>')

# ---------------------------------------------------------------- 1. circuit
def circuit():
    b = []
    # --- mic preamp: electret capsule + LM358 (full schematics in preamp-1 / preamp-2)
    b.append(R(30, 70, 375, 274))
    b.append(T(46, 94, "Mic preamp · electret + LM358", "tb"))
    b.append(R(352, 104, 43, 16, "res", 1))
    b.append(T(373, 99, "R0 220Ω", "ts", "middle"))
    b.append(L(352, 112, 225, 112, "w w-p3"))
    b.append(dot(340, 112)); b.append(dot(225, 112))
    b.append(L(340, 112, 340, 132, "w w-p3"))
    b.append(L(328, 132, 352, 132, "w w-ink2")); b.append(L(328, 139, 352, 139, "w w-ink2"))
    b.append(L(340, 139, 340, 152, "w w-gnd")); b.append(gnd(340, 152))
    b.append(T(340, 186, "C0 100µF", "ts", "middle"))
    b.append(L(225, 112, 225, 140, "w w-p3"))
    b.append(R(150, 140, 150, 110, "bx bx-acc"))
    b.append(T(225, 166, "LM358 preamp", "tb2", "middle"))
    b.append(T(225, 184, "R1 bias, 1 or 2 stages", "ts", "middle"))
    b.append(T(225, 200, "×101 (40 dB) or ×1100", "ts", "middle"))
    b.append(T(225, 216, "4.7 kΩ + 2.2 nF out", "ts", "middle"))
    b.append(T(225, 236, "see preamp diagrams", "ts", "middle"))
    b.append(L(225, 250, 225, 258, "w w-gnd")); b.append(gnd(225, 258))
    b.append('<circle cx="80" cy="215" r="16" class="cap"/>')
    b.append('<circle cx="80" cy="215" r="6" class="cap"/>')
    b.append(T(100, 196, "+", "ts")); b.append(T(100, 244, "−", "ts"))
    b.append(P("M80 199V185H150", "w w-sig"))
    b.append(L(80, 231, 80, 258, "w w-gnd")); b.append(gnd(80, 258))
    b.append(T(80, 296, "electret capsule", "ts", "middle"))
    b.append(T(46, 316, "Output ≈ 1.0 V DC + audio, never above ≈ 1.8 V (LM358 on 3.3 V).", "ts"))
    b.append(T(46, 331, "4.7 kΩ + 2.2 nF at the output: low-pass ≈ 15 kHz (anti-aliasing).", "ts"))
    # --- ESP32-S3
    b.append(R(420, 80, 220, 440, "bx bx-acc"))
    b.append(T(530, 106, "ESP32-S3-WROOM", "tb", "middle"))
    b.append(T(530, 124, "Freenove board", "ts", "middle"))
    b.append(T(430, 134, "3V3", "tm"))
    b.append(T(430, 174, "GND", "tm"))
    b.append(T(430, 214, "GPIO1 · ADC1", "tm"))
    for y, s in [(134, "5V"), (174, "GND"), (234, "GPIO11 · MOSI"), (274, "GPIO12 · SCLK"),
                 (314, "GPIO10 · CS"), (404, "GPIO14 · in"), (454, "GPIO21 · in")]:
        b.append(T(630, y, s, "tm", "end"))
    b.append(T(530, 362, "camera ribbon unplugged", "ts", "middle"))
    b.append(T(530, 486, "USB-C: 5 V in, serial", "ts", "middle"))
    b.append(T(530, 503, "UART0 · 921600 baud", "ts", "middle"))
    # preamp -> ESP connections
    b.append(P("M420 130H408V112H395", "w w-p3"))
    b.append(L(394, 170, 420, 170, "w w-gnd")); b.append(gnd(394, 170))
    b.append(L(300, 210, 420, 210, "w w-sig"))
    b.append(T(360, 203, "≈1.0 V + audio", "ts", "middle"))
    for y in (130, 170, 210): b.append(dot(420, y))
    # --- electrical test input (dashed)
    b.append(R(40, 360, 350, 310, "bx-dash"))
    b.append(T(56, 384, "Electrical test input", "tb"))
    b.append(T(56, 402, "use instead of the preamp on GPIO1", "ts"))
    b.append(T(56, 440, "Function generator", "ts"))
    b.append(T(56, 456, "sine, 1 Vpp, 0 V offset", "ts"))
    b.append(f'<circle cx="80" cy="520" r="20" class="bx"/>')
    b.append(T(80, 526, "~", "tb", "middle"))
    b.append(L(80, 540, 80, 612, "w w-gnd")); b.append(gnd(80, 612))
    # C1 series
    b.append(L(100, 520, 140, 520, "w w-sig"))
    b.append(L(140, 506, 140, 534, "w w-ink2")); b.append(L(148, 506, 148, 534, "w w-ink2"))
    b.append(L(148, 520, 200, 520, "w w-sig"))
    b.append(T(144, 498, "C1 10 µF", "ts", "middle"))
    b.append(dot(200, 520))
    # R1 up to 3V3
    b.append(L(200, 520, 200, 500, "w w-p3"))
    b.append(R(192, 440, 16, 60, "res", 1))
    b.append(L(200, 440, 200, 422, "w w-p3"))
    b.append(L(188, 422, 212, 422, "w w-p3"))
    b.append(T(218, 427, "3V3", "tm"))
    b.append(T(216, 474, "R1 10 kΩ", "ts"))
    # R2 down to GND
    b.append(L(200, 520, 200, 540, "w w-gnd"))
    b.append(R(192, 540, 16, 60, "res", 1))
    b.append(L(200, 600, 200, 612, "w w-gnd")); b.append(gnd(200, 612))
    b.append(T(216, 574, "R2 10 kΩ", "ts"))
    # R3 series
    b.append(L(200, 520, 226, 520, "w w-sig"))
    b.append(R(226, 512, 50, 16, "res", 1))
    b.append(L(276, 520, 310, 520, "w w-sig"))
    b.append(T(251, 504, "R3 1 kΩ", "ts", "middle"))
    b.append(dot(310, 520))
    # C2 shunt
    b.append(L(310, 520, 310, 560, "w w-gnd"))
    b.append(L(296, 560, 324, 560, "w w-ink2")); b.append(L(296, 568, 324, 568, "w w-ink2"))
    b.append(L(310, 568, 310, 612, "w w-gnd")); b.append(gnd(310, 612))
    b.append(T(322, 590, "C2 2.2 nF", "ts"))
    # to GPIO1 (dashed: alternative)
    b.append(P("M310 520L310 350L392 350L392 210", "w w-sig dash"))
    b.append(dot(392, 210))
    b.append(T(56, 642, "Bias 1.65 V · low-pass f_c ≈ 12 kHz (6 kΩ × 2.2 nF)", "ts"))
    b.append(T(56, 658, "High-pass ≈ 3 Hz (10 µF × 5 kΩ)", "ts"))
    # --- MAX7219
    b.append(R(780, 80, 230, 300))
    b.append(T(796, 104, "MAX7219 4-in-1 · 32 × 8", "tb"))
    for y, s in [(134, "VCC"), (174, "GND"), (234, "DIN"), (274, "CLK"), (314, "CS")]:
        b.append(T(790, y, s, "tm"))
    for i in range(4):
        gx = 850 + i * 38
        b.append(R(gx, 128, 34, 34, "grid", 2))
        dots = "".join(f'<circle cx="{gx + 4 + c * 3.75:.2f}" cy="{132 + r * 3.75:.2f}" r="1.1" class="led"/>'
                       for r in range(8) for c in range(8))
        b.append(dots)
        b.append(T(gx + 17, 178, f"#{i}", "ts", "middle"))
    b.append(T(850, 202, "DIN → #0 → #1 → #2 → #3", "ts"))
    b.append(T(850, 236, "Runs at 5 V, but its", "ts"))
    b.append(T(850, 252, "inputs get 3.3 V logic", "ts"))
    b.append(T(850, 268, "(spec: 3.5 V minimum).", "ts"))
    b.append(T(850, 292, "If pixels glitch, add", "ts"))
    b.append(T(850, 308, "a 74HCT125 buffer.", "ts"))
    b.append(T(850, 340, "SPI mode 0 · 1 MHz", "ts"))
    b.append(L(640, 130, 780, 130, "w w-p5")); b.append(T(700, 123, "5 V", "ts"))
    b.append(L(640, 170, 780, 170, "w w-gnd"))
    for y in (230, 270, 310):
        b.append(L(640, y, 780, y, "w w-spi"))
    for y in (130, 170, 230, 270, 310):
        b.append(dot(640, y)); b.append(dot(780, y))
    # --- buttons
    for y, name, desc in [(400, "SW1 · MODE", "short: mode · long: brightness"),
                          (450, "SW2 · LISTEN", "stops / restarts sampling")]:
        b.append(L(640, y, 700, y, "w w-ink2"))
        b.append(dot(640, y))
        b.append(f'<circle cx="702" cy="{y}" r="2.5" class="pin"/>')
        b.append(f'<circle cx="742" cy="{y}" r="2.5" class="pin"/>')
        b.append(L(704, y - 2, 738, y - 12, "w w-ink2"))
        b.append(L(721, y - 7, 721, y - 18, "w w-ink2"))
        b.append(L(713, y - 18, 729, y - 18, "w w-ink2"))
        b.append(L(744, y, 790, y, "w w-gnd")); b.append(gnd(790, y))
        b.append(T(812, y - 4, name, "tb2"))
        b.append(T(812, y + 12, desc, "ts"))
    b.append(T(812, 492, "internal pull-ups; pressed = GND", "ts"))
    # --- USB / laptop
    b.append(L(530, 520, 530, 590, "w w-ink2", "ink"))
    b.append(R(440, 590, 180, 56))
    b.append(T(530, 612, "Laptop", "tb", "middle"))
    b.append(T(530, 630, "power · flash · logs", "ts", "middle"))
    # --- legend
    lx, ly = 690, 560
    b.append(T(lx, ly, "Wires", "tb2"))
    for i, (cls, s) in enumerate([("w-p3", "3.3 V"), ("w-p5", "5 V"), ("w-gnd", "GND"),
                                  ("w-sig", "analogue signal"), ("w-spi", "SPI to display")]):
        yy = ly + 18 + i * 18 if i < 3 else ly + 18 + (i - 3) * 18
        xx = lx if i < 3 else lx + 150
        b.append(L(xx, yy - 4, xx + 28, yy - 4, f"w {cls}"))
        b.append(T(xx + 36, yy, s, "ts"))
    b.append(T(lx, ly + 84, "Dashed = alternative input, not both at once.", "ts"))
    return svg(1040, 690, "Spectrum visualiser · wiring", "".join(b))

# ---------------------------------------------------------------- 2. hardware overview
def hw_high():
    b = []
    y, h = 90, 100
    blocks = [
        (24, 170, "Sound source", ["voice, music, phone tone", "or function generator"], "bx"),
        (250, 190, "Input stage", ["electret + LM358 preamp", "or bias + RC test input"], "bx"),
        (520, 230, "ESP32-S3", ["samples at 40 kHz, FFT,", "maps 32 columns, reads buttons"], "bx bx-acc"),
        (800, 176, "LED display", ["4 × MAX7219, 32 × 8", "one column per band"], "bx"),
    ]
    for x, w, t, ls, c in blocks:
        b.append(box(x, y, w, h, t, ls, cls=c, center=True, title_dy=36, line_h=19))
    for x1, x2, lab, cls, ar in [(194, 250, "sound", "w w-sig", "sig"),
                                 (440, 520, "analogue", "w w-sig", "sig"),
                                 (750, 800, "SPI", "w w-spi", "spi")]:
        b.append(L(x1, y + h / 2, x2, y + h / 2, cls, ar))
        b.append(T((x1 + x2) / 2, y + h / 2 - 8, lab, "ts", "middle"))
    b.append(box(470, 270, 150, 64, "Buttons × 2", ["mode · listen"], center=True, title_dy=27, line_h=19))
    b.append(L(560, 270, 560, 190, "w w-ink2", "ink"))
    b.append(box(650, 270, 210, 64, "Laptop (USB-C)", ["5 V power · flash · serial logs"], center=True, title_dy=27, line_h=19))
    b.append(P("M700 270L700 190", "w w-ink2", "ink"))
    b.append(P("M700 190L700 270", "w w-ink2", "ink"))
    b.append(T(500, 372, "Power: USB 5 V → board 3.3 V regulator → ESP32-S3 and mic preamp. 5 V goes straight to the display.", "ts", "middle"))
    return svg(1000, 392, "Spectrum visualiser · hardware overview", "".join(b))

# ---------------------------------------------------------------- 3. hardware detail
def hw_low():
    b = []
    # ESP container
    b.append(R(240, 66, 520, 420, "ctr", 10))
    b.append(T(256, 90, "ESP32-S3 · dual core, 240 MHz", "tb"))
    # externals left
    b.append(box(24, 110, 196, 80, "Electret + LM358 preamp", ["gain ×101 or ×1100, no AGC", "out ≈ 1.0 V DC + audio"]))
    b.append(box(24, 250, 196, 70, "Buttons SW1, SW2", ["MODE, LISTEN · to GND"]))
    b.append(box(24, 400, 196, 70, "Laptop", ["idf.py monitor · tools/*.py"]))
    # internals
    b.append(box(260, 110, 140, 70, "ADC1", ["12-bit SAR, 12 dB", "continuous + DMA"], cls="bx"))
    b.append(box(430, 110, 160, 70, "Core 0", ["sampling + FFT", "one frame per 25.6 ms"], cls="bx bx-acc"))
    b.append(box(260, 250, 140, 70, "GPIO 14 / 21", ["pull-up inputs", "polled every 10 ms"]))
    b.append(box(430, 250, 160, 70, "Core 1", ["display at 40 fps", "+ buttons"], cls="bx bx-acc"))
    b.append(box(620, 250, 130, 70, "SPI2 master", ["mode 0, 1 MHz", "GPIO 11/12/10"]))
    b.append(box(260, 400, 140, 70, "UART0", ["921600 baud", "FRAME / TONE lines"]))
    b.append(box(620, 400, 130, 70, "Flash (NVS)", ["saved mode", "+ brightness"]))
    # arrows
    b.append(L(220, 145, 260, 145, "w w-sig", "sig")); b.append(T(240, 137, "GPIO1", "ts", "middle"))
    b.append(L(400, 145, 430, 145, "w w-sig", "sig"))
    b.append(L(510, 180, 510, 250, "w w-ink2", "ink")); b.append(T(518, 220, "1-slot queue", "ts"))
    b.append(L(220, 285, 260, 285, "w w-ink2", "ink"))
    b.append(L(400, 285, 430, 285, "w w-ink2", "ink"))
    b.append(L(590, 285, 620, 285, "w w-spi", "spi"))
    b.append(L(750, 285, 800, 285, "w w-spi", "spi"))
    b.append(P("M560 320L560 435L620 435", "w w-ink2", "ink"))
    b.append(P("M460 320L460 435L400 435", "w w-ink2", "ink"))
    b.append(L(260, 435, 220, 435, "w w-ink2", "ink"))
    # MAX7219 chain
    b.append(T(800, 228, "MAX7219 chain, 5 V", "tb2"))
    b.append(T(800, 246, "each chip: 8 row registers,", "ts"))
    b.append(T(800, 260, "intensity 0–15, no decode", "ts"))
    for i in range(4):
        yy = 268 + i * 52
        b.append(box(800, yy, 176, 36, f"#{i} · 8 × 8 LEDs", [], title_dy=23, pad=12, tcls="t"))
        if i < 3:
            b.append(L(888, yy + 36, 888, yy + 52, "w w-spi", "spi"))
    b.append(T(912, 316, "DOUT→DIN", "ts"))
    # power
    b.append(R(24, 510, 952, 66, "bx"))
    b.append(T(40, 534, "Power", "tb2"))
    b.append(T(40, 552, "USB 5 V → board 3.3 V regulator → ESP32-S3, and via a 220 Ω + 100 µF filter → mic preamp (keeps digital noise off the mic).", "ts"))
    b.append(T(40, 568, "USB 5 V → MAX7219 module. Its logic inputs get 3.3 V, below the 3.5 V spec: watch for glitches, buffer if needed.", "ts"))
    return svg(1000, 596, "Spectrum visualiser · hardware detail", "".join(b))

# ---------------------------------------------------------------- 4. firmware overview
def fw_high():
    b = []
    b.append(R(24, 64, 290, 40, "pill", 20)); b.append(T(169, 89, "Mic preamp → ADC1 (DMA, 40 kHz)", "ts", "middle"))
    b.append(R(524, 64, 290, 40, "pill", 20)); b.append(T(669, 89, "MAX7219 × 4 over SPI · 32 × 8", "ts", "middle"))
    # audio task
    b.append(R(24, 144, 290, 178, "bx bx-acc"))
    b.append(T(40, 168, "audio_task", "tmb"))
    b.append(T(40, 186, "core 0 · priority 6 · per 25.6 ms frame", "ts"))
    for i, s in enumerate(["adc_sampler_read()", "spectrum_compute()  · esp-dsp", "band_map_apply()",
                           "tone_find() + status flags"]):
        b.append(T(40, 214 + i * 22, s, "tm"))
    # queue
    b.append(R(344, 196, 150, 74, "bx q"))
    b.append(T(419, 220, "audio_frame_t", "tm", "middle"))
    b.append(T(419, 238, "1-slot queue", "ts", "middle"))
    b.append(T(419, 255, "newest frame wins", "ts", "middle"))
    # display task
    b.append(R(524, 144, 290, 178, "bx bx-acc"))
    b.append(T(540, 168, "display_task", "tmb"))
    b.append(T(540, 186, "core 1 · priority 5 · every 25 ms", "ts"))
    for i, s in enumerate(["bar_model_update()", "frame_draw_*()", "frame_to_device_rows()", "max7219_write_all()"]):
        b.append(T(540, 214 + i * 22, s, "tm"))
    # app_main
    b.append(R(844, 144, 132, 178))
    b.append(T(858, 168, "app_main", "tmb"))
    b.append(T(858, 186, "start-up order", "ts"))
    for i, s in enumerate(["1 settings", "2 queue", "3 display_task", "4 audio_task", "5 input_task"]):
        b.append(T(858, 210 + i * 21, s, "ts"))
    # input task
    b.append(R(344, 382, 300, 98, "bx bx-acc"))
    b.append(T(360, 406, "input_task", "tmb"))
    b.append(T(360, 424, "core 1 · priority 3 · every 10 ms", "ts"))
    b.append(T(360, 446, "button_poll() × 2", "tm"))
    b.append(T(360, 466, "settings_save()  · NVS", "tm"))
    # debug
    b.append(R(24, 382, 290, 98))
    b.append(T(40, 406, "debug_stream", "tmb"))
    b.append(T(40, 424, "FRAME / TONE / RATE lines", "ts"))
    b.append(T(40, 446, "UART 921600 → laptop", "ts"))
    b.append(T(40, 464, "tools/*.py → evidence plots", "ts"))
    # pills right of input
    b.append(R(674, 382, 140, 40, "pill", 20)); b.append(T(744, 407, "Buttons × 2", "ts", "middle"))
    b.append(R(674, 440, 140, 40, "pill", 20)); b.append(T(744, 465, "NVS flash", "ts", "middle"))
    # arrows
    b.append(L(169, 104, 169, 144, "w w-sig", "sig"))
    b.append(L(314, 233, 344, 233, "w w-ink2", "ink"))
    b.append(L(494, 233, 524, 233, "w w-ink2", "ink"))
    b.append(L(669, 144, 669, 104, "w w-spi", "spi"))
    b.append(L(169, 322, 169, 382, "w w-ink2", "ink"))
    b.append(P("M380 382L380 350L250 350L250 322", "w w-ink2", "ink"))
    b.append(T(388, 362, "set_mode · set_listening", "ts"))
    b.append(L(600, 382, 600, 322, "w w-ink2", "ink"))
    b.append(T(608, 362, "set_brightness", "ts"))
    b.append(L(674, 402, 644, 402, "w w-ink2", "ink"))
    b.append(L(644, 460, 674, 460, "w w-ink2", "ink"))
    b.append(T(500, 512, "Each driver is used by one task only, so the hardware needs no locks.", "ts", "middle"))
    return svg(1000, 530, "Spectrum visualiser · firmware overview", "".join(b))

# ---------------------------------------------------------------- 5. firmware detail
def fw_low():
    b = []
    audio = [
        ("adc_sampler_read()", "1024 raw 12-bit samples = 25.6 ms at 40 kHz (bass mode: 2048)"),
        ("frame stats", "min/max → clipping flag · RMS → silence flag"),
        ("remove DC", "subtract the frame mean (the preamp's ≈ 1.0 V bias)"),
        ("decimate · bass mode only", "63-tap Blackman low-pass, keep 1 in 4 → 10 kHz"),
        ("Hann window", "dsps_wind_hann_f32: less leakage into neighbouring columns"),
        ("FFT", "dsps_fft2r_fc32 + bit reversal, N = 1024 (bass 512)"),
        ("magnitude → dBFS", "512 bins × 39.1 Hz (bass 256 × 19.5 Hz); 0 dB = full-scale sine"),
        ("band_map_apply()", "loudest bin per column → 32 levels; hybrid log 100 Hz–8 kHz"),
        ("tone_find()", "peak bin + parabolic interpolation → frequency and column"),
        ("status + send", "above-range check · xQueueOverwrite · FRAME/TONE to serial"),
    ]
    disp = [
        ("xQueueReceive(…, 0)", "take the newest frame; none for 500 ms → blank"),
        ("choose view", "staircase after a rotate · not listening → blank · else bars"),
        ("bar_model_update()", "−46 dB floor, 3 dB/row: jumps up at once, falls 20 rows/s"),
        ("draw", "frame_draw_bar() for each of the 32 columns"),
        ("orientation", "k = 0..15 from NVS, changed by a long press on LISTEN"),
        ("frame_to_device_rows()", "apply the module's orientation flags"),
        ("max7219_write_all()", "4 chips × 8 rows over SPI; control registers re-sent every 1 s"),
    ]
    top, h, gap = 92, 50, 16
    b.append(T(24, 70, "audio_task · core 0 · once per captured frame (≈ 39 per s)", "tb2"))
    b.append(T(536, 70, "display_task · core 1 · every 25 ms (40 fps)", "tb2"))

    def column(x, w, steps, acc_idx=()):
        for i, (name, det) in enumerate(steps):
            y = top + i * (h + gap)
            cls = "bx bx-acc" if i in acc_idx else "bx"
            b.append(R(x, y, w, h, cls))
            b.append(T(x + 14, y + 21, name, "tmb"))
            b.append(T(x + 14, y + 39, det, "ts"))
            if i < len(steps) - 1:
                b.append(L(x + w / 2, y + h, x + w / 2, y + h + gap, "w w-sig" if x < 500 else "w w-ink2",
                           "sig" if x < 500 else "ink"))
        return top + (len(steps) - 1) * (h + gap)

    last_a = column(24, 464, audio, acc_idx=(5, 7))
    column(536, 440, disp)
    # queue connector: audio last -> display first
    ya = last_a + h / 2
    yd = top + h / 2
    b.append(P(f"M488 {ya}L512 {ya}L512 {yd}L536 {yd}", "w w-ink2", "ink"))
    yq = top + 7 * (h + gap) + 10
    b.append(R(536, yq, 440, 92, "bx q"))
    b.append(T(550, yq + 22, "audio_frame_t (the queue holds one)", "tmb"))
    b.append(T(550, yq + 41, "32 column levels · tone Hz + column · status bits · timestamp", "ts"))
    b.append(T(550, yq + 58, "If the display is late it skips old frames instead of lagging.", "ts"))
    b.append(T(550, yq + 75, "Shared between the two cores without locks.", "ts"))
    ym = top + 10 * (h + gap) + 12
    b.append(T(24, ym, "Modes (MODE button)", "tb2"))
    b.append(T(24, ym + 20, "FULL: hybrid log 100 Hz–8 kHz  ·  BASS/VOICE: decimated, 50 Hz–2.5 kHz  ·  LINEAR: baseline for comparison  (tone-finder hidden for now)", "ts"))
    return svg(1000, ym + 40, "Spectrum visualiser · firmware detail (one frame)", "".join(b))

# ---------------------------------------------------------------- 1b. LM358 preamp schematics
RAIL, GR = 110, 480

def vres(b, x, y1, y2, label=None, side="left"):
    """Vertical resistor on a wire from y1 to y2 (body 48 px, centred)."""
    m = (y1 + y2) / 2
    b.append(L(x, y1, x, m - 24, "w w-ink2")); b.append(R(x - 8, m - 24, 16, 48, "res", 1))
    b.append(L(x, m + 24, x, y2, "w w-ink2"))
    if label:
        if side == "left": b.append(T(x - 14, m + 4, label, "ts", "end"))
        else: b.append(T(x + 14, m + 4, label, "ts"))

def hres(b, x1, x2, y, label=None, cls="w w-sig"):
    m = (x1 + x2) / 2
    b.append(L(x1, y, m - 28, y, cls)); b.append(R(m - 28, y - 8, 56, 16, "res", 1))
    b.append(L(m + 28, y, x2, y, cls))
    if label: b.append(T(m, y - 14, label, "ts", "middle"))

def vcap(b, x, y, label=None, plus=False, side="right"):
    """Capacitor plates across a vertical wire at y (plates at y and y+7)."""
    b.append(L(x - 12, y, x + 12, y, "w w-ink2")); b.append(L(x - 12, y + 7, x + 12, y + 7, "w w-ink2"))
    if plus: b.append(T(x - 22, y - 2, "+", "ts"))
    if label:
        if side == "right": b.append(T(x + 18, y + 8, label, "ts"))
        else: b.append(T(x - 18, y + 8, label, "ts", "end"))

def hcap(b, x, y, label=None, plus_left=False):
    b.append(L(x, y - 12, x, y + 12, "w w-ink2")); b.append(L(x + 7, y - 12, x + 7, y + 12, "w w-ink2"))
    if plus_left: b.append(T(x - 10, y - 8, "+", "ts"))
    if label: b.append(T(x + 3, y - 18, label, "ts", "middle"))

def pinno(b, x, y, n):
    b.append(T(x, y, str(n), "pinno", "middle"))

def opamp_stage(b, x0, pins, rf, half, supply):
    """One non-inverting stage. x0 = bias column / + input node. Output node at x0+230, y 260."""
    pin_p, pin_n, pin_o = pins
    # bias divider
    b.append(dot(x0, RAIL)); vres(b, x0, RAIL, 230, "220 kΩ"); b.append(dot(x0, 230))
    vres(b, x0, 230, GR, "100 kΩ"); b.append(dot(x0, GR))
    # + input
    b.append(L(x0, 230, x0 + 90, 230, "w w-sig")); pinno(b, x0 + 78, 224, pin_p)
    # op-amp body
    b.append(f'<polygon points="{x0+90},200 {x0+90},320 {x0+190},260" class="bx bx-acc"/>')
    b.append(T(x0 + 99, 235, "+", "tb2")); b.append(T(x0 + 99, 296, "−", "tb2"))
    b.append(T(x0 + 128, 258, "LM358", "ts", "middle")); b.append(T(x0 + 128, 272, half, "ts", "middle"))
    # − input and gain leg
    b.append(P(f"M{x0+90} 290H{x0+50}V370", "w w-ink2")); pinno(b, x0 + 78, 284, pin_n)
    b.append(dot(x0 + 50, 370))
    b.append(L(x0 + 50, 370, x0 + 50, 384, "w w-ink2"))
    b.append(R(x0 + 42, 384, 16, 40, "res", 1)); b.append(T(x0 + 64, 408, "1 kΩ", "ts"))
    b.append(L(x0 + 50, 424, x0 + 50, 440, "w w-ink2"))
    vcap(b, x0 + 50, 440, "10 µF", plus=True)
    b.append(L(x0 + 50, 447, x0 + 50, GR, "w w-gnd")); b.append(dot(x0 + 50, GR))
    # feedback
    b.append(L(x0 + 50, 370, x0 + 150, 370, "w w-ink2"))
    b.append(R(x0 + 150, 362, 56, 16, "res", 1)); b.append(T(x0 + 178, 354, rf, "ts", "middle"))
    b.append(P(f"M{x0+206} 370H{x0+230}V260", "w w-ink2"))
    # output
    b.append(L(x0 + 190, 260, x0 + 230, 260, "w w-sig")); pinno(b, x0 + 204, 252, pin_o)
    b.append(dot(x0 + 230, 260))
    if supply:
        b.append(dot(x0 + 130, RAIL)); b.append(L(x0 + 130, RAIL, x0 + 130, 224, "w w-p3"))
        pinno(b, x0 + 140, 216, 8)
        # pin 4 to GND, hopping over the feedback wire
        b.append(P(f"M{x0+130} 296V362A8 8 0 0 1 {x0+130} 378V{GR}", "w w-gnd"))
        pinno(b, x0 + 140, 314, 4); b.append(dot(x0 + 130, GR))
        # decoupling at the chip
        b.append(dot(x0 + 168, RAIL)); b.append(L(x0 + 168, RAIL, x0 + 168, 146, "w w-p3"))
        vcap(b, x0 + 168, 146, "100 nF", side="right")
        b.append(L(x0 + 168, 153, x0 + 168, 160, "w w-gnd")); b.append(gnd(x0 + 168, 160))
        b.append(T(x0 + 186, 170, "at pins 8–4", "ts"))
    return x0 + 230

def preamp(stages):
    b = []
    x_s1 = 380
    out = opamp_stage(b, x_s1, (3, 2, 1), "Rf 100 kΩ", "half A", True)
    rail_end = x_s1 + 168
    if stages == 2:
        x_s2 = 720
        # C3 couples stage 1 out (≈1 V) into stage 2's own bias
        b.append(L(out, 260, 640, 260, "w w-sig")); hcap(b, 640, 260, "C3 1 µF", plus_left=False)
        b.append(P(f"M647 260H690V230H{x_s2}", "w w-sig"))
        out = opamp_stage(b, x_s2, (5, 6, 7), "Rf 10 kΩ", "half B", False)
        rail_end = x_s2
    # output filter
    xn = out + 130
    hres(b, out, xn, 260, "4.7 kΩ"); b.append(dot(xn, 260))
    b.append(L(xn, 260, xn, 350, "w w-gnd")); vcap(b, xn, 350, "2.2 nF")
    b.append(L(xn, 357, xn, GR, "w w-gnd")); b.append(dot(xn, GR))
    ex = xn + 90
    b.append(L(xn, 260, ex, 260, "w w-sig"))
    b.append(T((xn + ex) / 2, 252, "≈1.0 V + audio", "ts", "middle"))
    # ESP32-S3
    b.append(R(ex, 50, 190, 450, "bx bx-acc"))
    b.append(T(ex + 95, 100, "ESP32-S3", "tb", "middle"))
    b.append(T(ex + 95, 118, "Freenove board", "ts", "middle"))
    b.append(T(ex + 10, 74, "3V3", "tm")); b.append(T(ex + 10, 264, "GPIO1 · ADC1", "tm"))
    b.append(T(ex + 10, 484, "GND", "tm"))
    b.append(T(ex + 95, 330, "display GND: use a", "ts", "middle"))
    b.append(T(ex + 95, 345, "different GND pin", "ts", "middle"))
    for y in (70, 260, GR): b.append(dot(ex, y))
    # unfiltered 3V3 -> R0 -> filtered rail, C0
    b.append(P(f"M{ex} 70H56V{RAIL}H76", "w w-p3"))
    b.append(T(ex - 12, 62, "3V3 from the board (noisy)", "ts", "end"))
    hres(b, 76, 140, RAIL, None, "w w-p3"); b.append(T(108, 96, "R0 220 Ω", "ts", "middle"))
    b.append(dot(140, RAIL))
    b.append(L(140, RAIL, rail_end, RAIL, "w w-p3"))
    b.append(T(rail_end + 12, RAIL + 4, "filtered 3.3 V rail", "ts"))
    b.append(L(140, RAIL, 140, 290, "w w-p3")); vcap(b, 140, 290, "C0", plus=True, side="left")
    b.append(T(122, 314, "100 µF", "ts", "end"))
    b.append(L(140, 297, 140, GR, "w w-gnd")); b.append(dot(140, GR))
    # GND rail
    b.append(L(140, GR, ex, GR, "w w-gnd"))
    b.append(T(150, GR + 18, "GND rail", "ts"))
    # mic
    xm = 230
    b.append(dot(xm, RAIL)); vres(b, xm, RAIL, 230, "R1 2.2 kΩ", side="right"); b.append(dot(xm, 230))
    b.append(L(xm, 230, xm, 274, "w w-sig"))
    b.append(f'<circle cx="{xm}" cy="290" r="16" class="cap"/>')
    b.append(f'<circle cx="{xm}" cy="290" r="6" class="cap"/>')
    b.append(T(xm + 20, 276, "+", "ts")); b.append(T(xm + 20, 314, "−", "ts"))
    b.append(L(xm, 306, xm, GR, "w w-gnd")); b.append(dot(xm, GR))
    b.append(T(xm + 26, 296, "electret", "ts")); b.append(T(xm + 26, 330, "− = case pin", "ts"))
    b.append(L(xm, 230, 300, 230, "w w-sig")); hcap(b, 300, 230, "C1 1 µF", plus_left=True)
    b.append(L(307, 230, x_s1, 230, "w w-sig"))
    # gain notes under the stages
    b.append(T(x_s1 + 115, GR + 36, "Stage 1: gain 1 + 100k/1k ≈ ×101 (40 dB)", "tb2", "middle"))
    if stages == 2:
        b.append(T(720 + 115, GR + 36, "Stage 2: 1 + 10k/1k ≈ ×11 (21 dB)", "tb2", "middle"))
        b.append(T(560, GR + 56, "Total ≈ ×1100 (61 dB). Loud sound will clip: the bars stop at the top.", "ts", "middle"))
    else:
        b.append(T(x_s1 + 115, GR + 56, "10 µF keeps DC gain at 1, so pin 1 sits at the ≈1.0 V bias", "ts", "middle"))
    W = ex + 190 + 30
    # ---- bottom panels: DC check · chip pins · build tips
    py = 560
    pw = (W - 24 * 2 - 20 * 2) / 3
    xs = [24 + i * (pw + 20) for i in range(3)]
    ph = 290
    for x in xs: b.append(R(x, py, pw, ph))
    # DC check
    x = xs[0] + 16
    b.append(T(x, py + 24, "1 · DC check before plugging into GPIO1", "tb2"))
    b.append(T(x, py + 42, "Power on, room quiet, meter black lead on GND.", "ts"))
    rows = [("pin 8 (filtered rail)", "≈ 3.0–3.2 V"), ("mic +", "≈ 2.0–2.8 V"),
            ("pin 3" + (", pin 5" if stages == 2 else ""), "≈ 0.95 V"),
            ("pin 2" + (", pin 6" if stages == 2 else ""), "same as pin 3"),
            ("pin 1" + (", pin 7" if stages == 2 else ""), "≈ 0.9–1.1 V"),
            ("GPIO1", "same as pin " + ("7" if stages == 2 else "1"))]
    for i, (k, v) in enumerate(rows):
        yy = py + 68 + i * 22
        b.append(T(x, yy, k, "tm")); b.append(T(xs[0] + pw - 16, yy, v, "tm", "end"))
        b.append(L(x, yy + 7, xs[0] + pw - 16, yy + 7, "w rule"))
    b.append(T(x, py + 216, "Output near 0 V or ≥ 1.7 V = stage stuck:", "ts"))
    b.append(T(x, py + 232, "check Rf, the 1 kΩ + 10 µF leg and the", "ts"))
    b.append(T(x, py + 248, "10 µF polarity; pin 3 not ≈ 0.95 V → check", "ts"))
    b.append(T(x, py + 264, "the 220 k / 100 k divider and C1.", "ts"))
    # chip pins
    x = xs[1]
    b.append(T(x + 16, py + 24, "2 · LM358 from above (notch at top)", "tb2"))
    cx, cy, cw, chh = x + pw / 2 - 30, py + 54, 60, 150
    b.append(R(cx, cy, cw, chh, "bx bx-acc", 4))
    b.append(f'<path d="M{cx+20} {cy}A10 10 0 0 0 {cx+40} {cy}" class="w"/>')
    b.append(f'<circle cx="{cx+12}" cy="{cy+14}" r="3" class="dot"/>')
    left = [(1, "OUT A", "Rf, 4.7 kΩ" if stages == 1 else "Rf, C3"),
            (2, "IN A−", "Rf, 1 kΩ"), (3, "IN A+", "C1, bias"), (4, "GND", "GND rail")]
    right = [(8, "VCC", "filtered 3.3 V"),
             (7, "OUT B", "→ pin 6" if stages == 1 else "Rf 10k, 4.7 kΩ"),
             (6, "IN B−", "→ pin 7" if stages == 1 else "Rf 10k, 1 kΩ"),
             (5, "IN B+", "→ GND" if stages == 1 else "C3, bias")]
    for i, (n, nm, to) in enumerate(left):
        yy = cy + 22 + i * 36
        b.append(L(cx - 10, yy, cx, yy, "w w-ink2")); pinno(b, cx + 9, yy + 4, n)
        b.append(T(cx - 14, yy - 2, nm, "tm", "end")); b.append(T(cx - 14, yy + 12, to, "ts", "end"))
    for i, (n, nm, to) in enumerate(right):
        yy = cy + 22 + i * 36
        b.append(L(cx + cw, yy, cx + cw + 10, yy, "w w-ink2")); pinno(b, cx + cw - 9, yy + 4, n)
        b.append(T(cx + cw + 14, yy - 2, nm, "tm")); b.append(T(cx + cw + 14, yy + 12, to, "ts"))
    b.append(T(x + pw / 2, py + 230, "100 nF straight across pins 8 and 4.", "ts", "middle"))
    b.append(T(x + pw / 2, py + 246, "One-stage build: tie off half B" if stages == 1 else "Both halves are in the same chip:",
               "ts", "middle"))
    b.append(T(x + pw / 2, py + 262, "(7 → 6, 5 → GND) so it can't oscillate." if stages == 1 else "pins 8 and 4 power both.",
               "ts", "middle"))
    # tips
    x = xs[2] + 16
    b.append(T(x, py + 24, "3 · Build tips", "tb2"))
    tips = ["Breadboard + rail = filtered 3.3 V only (after R0),",
            "− rail = GND. Nothing else on these rails.",
            "One wire GND rail → an ESP GND pin; the display",
            "GND goes to a different ESP GND pin.",
            "Electrolytics: C0 + to the rail, C1 + to the mic,",
            "10 µF + to the 1 kΩ (pin side).",
            "Mic leads short; − is the pin joined to the case.",
            ("Function generator: mic out, ≤ 10 mVpp into C1" if stages == 1
             else "Function generator: mic out, ≤ 1 mVpp into C1"),
            ("(×101 → ≈ 1 Vpp at pin 1)." if stages == 1
             else "(100:1 divider: 10 kΩ then 100 Ω to GND)."),
            ]
    ys = [48, 66, 94, 112, 140, 158, 186, 214, 232]
    for yy, t in zip(ys, tips):
        b.append(T(x, py + yy, t, "ts"))
    H = py + ph + 20
    name = "one stage (×101)" if stages == 1 else "two stages (×1100)"
    return svg(int(W), H, f"Mic preamp · LM358, {name}", "".join(b))

def preamp1(): return preamp(1)
def preamp2(): return preamp(2)

# ---------------------------------------------------------------- 4b. software flowchart
def fc_proc(b, cx, y, w, h, lines, cls="bx"):
    b.append(R(cx - w / 2, y, w, h, cls, 4))
    n = len(lines); top = y + h / 2 - (n - 1) * 8 + 4
    for i, s in enumerate(lines):
        b.append(T(cx, top + i * 16, s, "t" if i == 0 else "ts", "middle"))

def fc_io(b, cx, y, w, h, lines):
    k = 10
    x1, x2 = cx - w / 2, cx + w / 2
    b.append(f'<polygon points="{x1+k},{y} {x2+k},{y} {x2-k},{y+h} {x1-k},{y+h}" class="bx io"/>')
    n = len(lines); top = y + h / 2 - (n - 1) * 8 + 4
    for i, s in enumerate(lines):
        b.append(T(cx, top + i * 16, s, "t" if i == 0 else "ts", "middle"))

def fc_dec(b, cx, cy, w, h, lines):
    b.append(f'<polygon points="{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}" class="dec"/>')
    n = len(lines); top = cy - (n - 1) * 7 + 4
    for i, s in enumerate(lines):
        b.append(T(cx, top + i * 14, s, "tb2", "middle"))

def fc_term(b, cx, y, w, h, text):
    b.append(R(cx - w / 2, y, w, h, "bx bx-acc", h / 2))
    b.append(T(cx, y + h / 2 + 5, text, "tb2", "middle"))

def fw_flow():
    b = []
    A = lambda d: P(d, "w w-ink2", "ink")
    # start + app_main
    fc_term(b, 500, 60, 220, 34, "Power on / reset")
    b.append(L(500, 94, 500, 112, "w w-ink2", "ink"))
    fc_proc(b, 500, 112, 660, 52, ["app_main (runs once)",
            "load settings from NVS → create 1-slot queue → start display, audio and input tasks"])
    b.append(L(500, 164, 500, 184, "w w-ink2"))
    b.append(L(170, 186, 720, 186, "w fork"))
    b.append(L(170, 188, 170, 214, "w w-ink2", "ink")); b.append(L(720, 188, 720, 214, "w w-ink2", "ink"))
    b.append(T(728, 204, "the three tasks then run side by side, for ever", "ts"))
    # lanes
    b.append(R(24, 214, 400, 560, "ctr", 10)); b.append(R(576, 214, 400, 500, "ctr", 10))
    b.append(T(40, 238, "audio_task", "tmb")); b.append(T(40, 255, "core 0 · one pass per 25.6 ms of sound", "ts"))
    b.append(T(592, 238, "display_task", "tmb")); b.append(T(592, 255, "core 1 · one pass every 25 ms (40 fps)", "ts"))
    # ---- audio lane (main x 170, side x 348)
    M, S = 170, 348
    fc_proc(b, M, 270, 230, 40, ["Start ADC1 on GPIO1", "40 kHz, DMA into a buffer"])
    b.append(L(M, 310, M, 338, "w w-ink2", "ink")); b.append(dot(M, 326))
    fc_dec(b, M, 366, 160, 56, ["Mode", "changed?"])
    b.append(L(M + 80, 366, S - 52, 366, "w w-ink2", "ink")); b.append(T(M + 90, 359, "Yes", "lbl"))
    fc_proc(b, S, 346, 104, 40, ["Set FFT size", "+ column map"])
    b.append(A(f"M{S} 386V414H{M+6}")); b.append(L(M, 394, M, 414, "w w-ink2")); b.append(T(M + 6, 408, "No", "lbl"))
    b.append(dot(M, 414)); b.append(L(M, 414, M, 426, "w w-ink2", "ink"))
    fc_dec(b, M, 454, 160, 56, ["Listening?"])
    b.append(L(M + 80, 454, S - 52, 454, "w w-ink2", "ink")); b.append(T(M + 90, 447, "No", "lbl"))
    fc_proc(b, S, 434, 104, 40, ["Blank frame", "wait 100 ms"])
    b.append(A(f"M{S+52} 454H412V326H{M+6}"))
    b.append(L(M, 482, M, 502, "w w-ink2", "ink")); b.append(T(M + 6, 496, "Yes", "lbl"))
    fc_io(b, M, 502, 230, 40, ["Read 1024 samples", "25.6 ms of sound"])
    b.append(L(M, 542, M, 562, "w w-ink2", "ink"))
    fc_proc(b, M, 562, 230, 40, ["Remove DC · Hann window · FFT", "512 bins in dB, 39 Hz each"])
    b.append(L(M, 602, M, 622, "w w-ink2", "ink"))
    fc_proc(b, M, 622, 230, 40, ["Bins → 32 column levels", "loudest bin in each column"])
    b.append(L(M, 662, M, 682, "w w-ink2", "ink"))
    fc_io(b, M, 682, 230, 48, ["Put frame in the queue", "(replaces any unread one)"])
    b.append(A(f"M{M} 730V752H38V326H{M-6}"))
    # queue
    b.append(R(440, 520, 120, 80, "bx q"))
    b.append(T(500, 545, "Queue", "tmb", "middle")); b.append(T(500, 563, "1 slot", "ts", "middle"))
    b.append(T(500, 579, "newest frame wins", "ts", "middle"))
    b.append(A(f"M{M+115} 706H500V600"))
    b.append(A("M500 520V440H640"))
    # ---- display lane (main x 720, side x 902)
    M, S = 720, 902
    fc_proc(b, M, 270, 230, 40, ["Start SPI2 + 4 × MAX7219", "1 MHz, brightness from NVS"])
    b.append(L(M, 310, M, 346, "w w-ink2", "ink")); b.append(dot(M, 326))
    fc_proc(b, M, 346, 230, 48, ["Wait for the 25 ms tick", "apply new brightness / rotation"])
    b.append(L(M, 394, M, 412, "w w-ink2", "ink"))
    fc_dec(b, M, 440, 160, 56, ["New frame", "in queue?"])
    b.append(L(M + 80, 440, S - 52, 440, "w w-ink2", "ink")); b.append(T(M + 90, 433, "No", "lbl"))
    fc_proc(b, S, 420, 104, 40, ["No frame for", "0.5 s → blank"])
    b.append(A(f"M{S} 460V494H{M+6}")); b.append(L(M, 468, M, 494, "w w-ink2")); b.append(T(M + 6, 486, "Yes", "lbl"))
    b.append(dot(M, 494)); b.append(L(M, 494, M, 514, "w w-ink2", "ink"))
    fc_proc(b, M, 514, 230, 48, ["Bar rows = (dB − floor) ÷ 3 dB", "jump up at once, fall 20 rows/s"])
    b.append(L(M, 562, M, 582, "w w-ink2", "ink"))
    fc_proc(b, M, 582, 230, 40, ["Draw 32 bars", "then apply the rotation"])
    b.append(L(M, 622, M, 642, "w w-ink2", "ink"))
    fc_io(b, M, 642, 230, 40, ["Send 8 rows × 4 chips", "over SPI"])
    b.append(A(f"M{M} 682V700H966V326H{M+6}"))
    # ---- input strip
    b.append(R(24, 800, 952, 170, "ctr", 10))
    b.append(T(40, 824, "input_task", "tmb")); b.append(T(130, 824, "core 1 · one pass every 10 ms", "ts"))
    cy = 892
    b.append(dot(60, cy))
    b.append(L(60, cy, 80, cy, "w w-ink2", "ink"))
    fc_proc(b, 140, cy - 22, 120, 44, ["Wait 10 ms"])
    b.append(L(200, cy, 230, cy, "w w-ink2", "ink"))
    fc_io(b, 310, cy - 22, 150, 44, ["Read both buttons", "debounced"])
    b.append(L(385, cy, 410, cy, "w w-ink2", "ink"))
    fc_dec(b, 470, cy, 120, 60, ["Pressed?"])
    b.append(L(530, cy, 560, cy, "w w-ink2", "ink")); b.append(T(536, cy - 7, "Yes", "lbl"))
    b.append(R(560, cy - 52, 240, 104, "bx", 4))
    acts = [("MODE short", "next mode"), ("MODE long", "next brightness"),
            ("LISTEN short", "stop / start"), ("LISTEN long", "rotate display")]
    for i, (k, v) in enumerate(acts):
        yy = cy - 28 + i * 20
        b.append(T(574, yy, k, "tm")); b.append(T(676, yy, "→ " + v, "ts"))
    b.append(L(800, cy, 822, cy, "w w-ink2", "ink"))
    fc_proc(b, 890, cy - 22, 136, 44, ["Save to NVS", "kept after power-off"])
    b.append(A(f"M890 {cy+22}V952H60V{cy+4}"))
    b.append(A(f"M470 {cy+30}V952")); b.append(T(476, cy + 46, "No", "lbl")); b.append(dot(470, 952))
    # requests up into the other tasks (atomic flags, read at the start of each pass)
    b.append(P(f"M610 {cy-52}V786H250V776", "w w-ink2 dash", "ink"))
    b.append(T(618, 820, "mode, listening", "ts"))
    b.append(P(f"M760 {cy-52}V716", "w w-ink2 dash", "ink"))
    b.append(T(768, 760, "brightness, rotation", "ts"))
    # legend
    ly = 1000
    b.append(T(24, ly, "Shapes:", "tb2"))
    lx = 90
    b.append(R(lx, ly - 14, 40, 18, "bx bx-acc", 9)); b.append(T(lx + 48, ly, "start", "ts"))
    lx += 100
    b.append(R(lx, ly - 14, 40, 18, "bx", 3)); b.append(T(lx + 48, ly, "step", "ts"))
    lx += 96
    b.append(f'<polygon points="{lx+20},{ly-16} {lx+40},{ly-5} {lx+20},{ly+6} {lx},{ly-5}" class="dec"/>')
    b.append(T(lx + 48, ly, "decision", "ts"))
    lx += 116
    b.append(f'<polygon points="{lx+6},{ly-14} {lx+46},{ly-14} {lx+34},{ly+4} {lx-6},{ly+4}" class="bx io"/>')
    b.append(T(lx + 54, ly, "hardware in / out", "ts"))
    lx += 170
    b.append(R(lx, ly - 14, 40, 18, "bx q", 3)); b.append(T(lx + 48, ly, "queue between cores", "ts"))
    lx += 180
    b.append(L(lx, ly - 5, lx + 36, ly - 5, "w w-ink2 dash", "ink")); b.append(T(lx + 44, ly, "button request (a flag)", "ts"))
    return svg(1000, 1020, "Spectrum visualiser · software flowchart", "".join(b))

DIAGRAMS = [
    ("circuit", "Wiring", "Every connection, with the electrical test input as the alternative to the mic. Pin order on the modules is drawn for clarity, not as the physical header order.", circuit),
    ("preamp-1", "Mic preamp: LM358, one stage", "Electret capsule into one LM358 stage (gain ×101), with the DC readings to check and the chip pins. Start here.", preamp1),
    ("preamp-2", "Mic preamp: LM358, two stages", "Same as one stage, then the chip's second half adds ×11 (total ×1100) for a quiet capsule.", preamp2),
    ("hw-overview", "Hardware overview", "What each part does and how signals move between them.", hw_high),
    ("hw-detail", "Hardware detail", "Inside the ESP32-S3: which peripheral handles each signal, and where each core does its work.", hw_low),
    ("fw-flow", "Software flowchart", "What the firmware does from power-on: start-up once, then three tasks looping side by side. The queue is the only link between sound and display.", fw_flow),
    ("fw-overview", "Firmware overview", "Three FreeRTOS tasks, what each owns, and how they talk.", fw_high),
    ("fw-detail", "Firmware detail", "What happens to one captured frame, from raw samples to LEDs.", fw_low),
]

LIGHT = dict(bg="#f4f6f8", panel="#ffffff", ctr="#eef2f6", ink="#16202b", ink2="#3d4a59", muted="#5d6b7b",
             line="#9aa7b5", acc="#1f6f8b", acct="#e3f0f5", sig="#0f7b6c", spi="#3655b3", p3="#c2410c",
             p5="#b3261e", gnd="#55606d", led="#c8302c", q="#fff7e0", qline="#b98a12")

STYLE_RULES = """
.t{fill:VAR(ink);font:13px FONT}
.th{fill:VAR(ink);font:600 17px FONT}
.tb{fill:VAR(ink);font:600 14px FONT}
.tb2{fill:VAR(ink);font:600 13px FONT}
.ts{fill:VAR(muted);font:11.5px FONT}
.tm{fill:VAR(ink);font:12px MONO}
.tmb{fill:VAR(ink);font:600 12.5px MONO}
.bx{fill:VAR(panel);stroke:VAR(line);stroke-width:1.2}
.bx-acc{fill:VAR(acct);stroke:VAR(acc);stroke-width:1.6}
.bx-dash{fill:none;stroke:VAR(line);stroke-width:1.2;stroke-dasharray:6 4}
.ctr{fill:VAR(ctr);stroke:VAR(line);stroke-width:1.2}
.q{fill:VAR(q);stroke:VAR(qline)}
.pill{fill:VAR(panel);stroke:VAR(line);stroke-width:1.2}
.res{fill:VAR(panel);stroke:VAR(ink2);stroke-width:1.5}
.cap{fill:none;stroke:VAR(ink2);stroke-width:1.5}
.grid{fill:#16181b;stroke:VAR(line)}
.led{fill:VAR(led)}
.pin{fill:VAR(panel);stroke:VAR(ink2);stroke-width:1.5}
.w{fill:none;stroke:VAR(ink2);stroke-width:1.6}
.w-ink2{stroke:VAR(ink2)}
.w-sig{stroke:VAR(sig);stroke-width:2}
.w-spi{stroke:VAR(spi);stroke-width:2}
.w-p3{stroke:VAR(p3);stroke-width:2}
.w-p5{stroke:VAR(p5);stroke-width:2}
.w-gnd{stroke:VAR(gnd)}
.dash{stroke-dasharray:6 4}
.dec{fill:VAR(q);stroke:VAR(qline);stroke-width:1.4}
.io{stroke:VAR(sig);stroke-width:1.4}
.fork{stroke:VAR(ink2);stroke-width:5}
.rule{stroke:VAR(line);stroke-width:0.8}
.lbl{fill:VAR(acc);font:600 11.5px FONT}
.pinno{fill:VAR(acc);font:600 11px MONO}
.dot{fill:VAR(ink2)}
.mk{fill:VAR(ink2)}
.mk-sig{fill:VAR(sig)}
.mk-spi{fill:VAR(spi)}
"""
FONT = "'IBM Plex Sans','DejaVu Sans',Arial,sans-serif"
MONO = "'IBM Plex Mono','DejaVu Sans Mono',Consolas,monospace"

def style_with(values):
    css = STYLE_RULES.replace("FONT", FONT).replace("MONO", MONO)
    import re
    return re.sub(r"VAR\((\w+)\)", lambda m: values[m.group(1)], css)

def style_tokens():
    css = STYLE_RULES.replace("FONT", "var(--sans)").replace("MONO", "var(--mono)")
    import re
    return re.sub(r"VAR\((\w+)\)", lambda m: f"var(--d-{m.group(1)})", css)

def main():
    os.makedirs(os.path.join(OUT, "svg"), exist_ok=True)
    rendered = []
    for slug, title, cap, fn in DIAGRAMS:
        w, h, label, body = fn()
        s = page_svg(w, h, label, body)
        rendered.append((slug, title, cap, s))
        standalone = report_svg(w, h, label, body, style_with(LIGHT), LIGHT["bg"])
        with open(os.path.join(OUT, "svg", f"{slug}.svg"), "w") as f:
            f.write(standalone)
    with open(os.path.join(OUT, "page_template.html")) as f:
        page = f.read()
    sections = []
    for slug, title, cap, s in rendered:
        sections.append(f'<section class="fig" id="{slug}"><header><h2>{esc(title)}</h2>'
                        f'<p>{esc(cap)}</p></header><div class="scroll">{s}</div></section>')
    page = page.replace("/*DIAGRAM_CSS*/", style_tokens()).replace("<!--SECTIONS-->", "\n".join(sections))
    with open(os.path.join(OUT, "diagrams.html"), "w") as f:
        f.write(page)
    print("ok")

if __name__ == "__main__":
    main()
