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
    # --- MAX9814 module
    b.append(R(40, 80, 210, 204))
    b.append(T(56, 104, "MAX9814 mic module", "tb"))
    b.append(f'<circle cx="92" cy="168" r="22" class="cap"/>')
    b.append(f'<circle cx="92" cy="168" r="9" class="cap"/>')
    b.append(T(92, 204, "electret capsule", "ts", "middle"))
    b.append(T(240, 134, "VDD", "tm", "end"))
    b.append(T(240, 174, "GND", "tm", "end"))
    b.append(T(240, 214, "OUT", "tm", "end"))
    b.append(T(56, 238, "Gain pin: open 60 dB,", "ts"))
    b.append(T(56, 254, "GND 50 dB, VDD 40 dB", "ts"))
    b.append(T(56, 270, "A/R open · AGC on chip", "ts"))
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
    # mic -> ESP wires
    b.append(L(250, 130, 420, 130, "w w-p3"))
    b.append(T(300, 123, "3.3 V", "ts"))
    b.append(L(250, 170, 420, 170, "w w-gnd"))
    b.append(L(250, 210, 420, 210, "w w-sig"))
    b.append(T(338, 203, "0.25–2.25 V", "ts", "middle"))
    for y in (130, 170, 210):
        b.append(dot(250, y)); b.append(dot(420, y))
    # --- electrical test input (dashed)
    b.append(R(40, 360, 350, 310, "bx-dash"))
    b.append(T(56, 384, "Electrical test input", "tb"))
    b.append(T(56, 402, "use instead of the mic on GPIO1", "ts"))
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
    b.append(P("M310 520L310 210", "w w-sig dash"))
    b.append(dot(310, 210))
    b.append(T(302, 326, "to GPIO1 instead of mic OUT", "ts", "end"))
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
        (250, 190, "Input stage", ["MAX9814 mic + AGC", "or bias + RC test input"], "bx"),
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
    b.append(T(500, 372, "Power: USB 5 V → board 3.3 V regulator → ESP32-S3 and mic.  5 V goes straight to the display.", "ts", "middle"))
    return svg(1000, 392, "Spectrum visualiser · hardware overview", "".join(b))

# ---------------------------------------------------------------- 3. hardware detail
def hw_low():
    b = []
    # ESP container
    b.append(R(240, 66, 520, 420, "ctr", 10))
    b.append(T(256, 90, "ESP32-S3 · dual core, 240 MHz", "tb"))
    # externals left
    b.append(box(24, 110, 196, 80, "MAX9814 + capsule", ["preamp + AGC, 40/50/60 dB", "out 1.25 V ± 1 V max"]))
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
    b.append(T(40, 552, "USB 5 V → board 3.3 V regulator → ESP32-S3 and MAX9814 (3.3 V keeps the mic output inside the ADC range).", "ts"))
    b.append(T(40, 568, "USB 5 V → MAX7219 module. Its logic inputs get 3.3 V, below the 3.5 V spec: watch for glitches, buffer if needed.", "ts"))
    return svg(1000, 596, "Spectrum visualiser · hardware detail", "".join(b))

# ---------------------------------------------------------------- 4. firmware overview
def fw_high():
    b = []
    b.append(R(24, 64, 290, 40, "pill", 20)); b.append(T(169, 89, "MAX9814 → ADC1 (DMA, 40 kHz)", "ts", "middle"))
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
        ("remove DC", "subtract the frame mean (the mic's ≈ 1.25 V bias)"),
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
        ("choose view", "not listening → blank · tone-finder → digits · else bars"),
        ("bar_model_update()", "−60 dB floor, 4 dB/row, falls 20 rows/s, peaks hold 0.5 s"),
        ("draw", "frame_draw_bar / _peak, or “440Hz” + a marker at its column"),
        ("frame_draw_status()", "top-right, right→left: silent · clip · above range · not listening"),
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
    b.append(T(24, ym + 20, "FULL: hybrid log 100 Hz–8 kHz  ·  BASS/VOICE: decimated, 50 Hz–2.5 kHz  ·  TONE-FINDER: frequency as digits  ·  LINEAR: baseline for comparison", "ts"))
    return svg(1000, ym + 40, "Spectrum visualiser · firmware detail (one frame)", "".join(b))

DIAGRAMS = [
    ("circuit", "Wiring", "Every connection, with the electrical test input as the alternative to the mic. Pin order on the modules is drawn for clarity, not as the physical header order.", circuit),
    ("hw-overview", "Hardware overview", "What each part does and how signals move between them.", hw_high),
    ("hw-detail", "Hardware detail", "Inside the ESP32-S3: which peripheral handles each signal, and where each core does its work.", hw_low),
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
