# Lab tests — what to run, what to record, what it sets

Checklist for lab sessions. Claude keeps this updated with every commit; tick items off and note the evidence file name.
Each test either **sets a value** in `main/app_config.h` (marked MEASURE there) or **produces evidence** for the report (or both).
After a test sets a value: change it in `app_config.h`, add a decision-log line in `docs/PLAN.md` citing the log file.

**Before anything:** camera ribbon unplugged · `. $IDF_PATH/export.sh` · if you built before 29/10 afternoon, delete `sdkconfig` (and `bringup/*/sdkconfig`) once so the 921600 baud setting applies.

Log names: `docs/evidence/logs/YYYY-MM-DD_<test>.txt` — capture with `tools/capture.sh <test>` (or `idf.py -p /dev/ttyACM0 monitor | tee <file>`).
Analysis: `source .venv/bin/activate` then the `tools/` scripts named under each test (see `tools/README.md`).

---

## Session A — bring-ups (code ready now)

### A1. Matrix bring-up — `bringup/01_matrix`

```bash
cd bringup/01_matrix && idf.py set-target esp32s3   # first time only
idf.py build flash -p /dev/ttyACM0 monitor | tee ../../docs/evidence/logs/2026-10-29_01_matrix.txt
```

Wiring: VCC → 5V, GND → GND, DIN → 11, CS → 10, CLK → 12.

- [ ] STEP 1 photo: all LEDs on → `photos/..._01_testmode.jpg`
- [ ] STEP 2 photos A, B, C (single LEDs) → which chip is chip 0, which corner
- [x] STEP 3 probe (05/11, `2026-11-05_A1_probe.txt`, photos `2026-11-05_A1_Probe_P3/P4.jpeg`): P2 left of O, P3 below O, O in the rightmost module, P4 next left
  → **set** `APP_ORIENT_REVERSE_DEVICES` 1 / `FLIP_X` 0 / `FLIP_Y` 1 / `TRANSPOSE` 0 (table in `bringup/README.md`)
- [ ] Reflash with the flags set (it runs steps 1–3 again first, ~75 s, then STEP 4), soak 5 min: staircase rises bottom-left → top-right?: any random pixels? note `write_avg` / `write_max`. The bring-up does **not** re-send control registers, so any glitch stays visible here (the main firmware re-sends them every second)
  → evidence for the 3.3 V-logic risk; `write_avg` goes in the latency budget
- [ ] Optional: soak again at `APP_MAX7219_CLOCK_HZ` = 4 MHz and 10 MHz → **sets** the clock (fastest clean one, or stay at 1 MHz)

### A2. Mic + ADC bring-up — `bringup/02_mic_adc`

```bash
cd bringup/02_mic_adc && idf.py set-target esp32s3   # first time only
idf.py build flash -p /dev/ttyACM0 monitor | tee ../../docs/evidence/logs/2026-10-29_02_rate_sweep.txt
```

Wiring: electret capsule + LM358 preamp, op-amp output → 4.7 kΩ → GPIO 1 — parts table in `bringup/README.md`, schematics in `docs/diagrams/preamp-1.png` / `preamp-2.png`. First measure the output in a quiet room (want 0.9–1.1 V, same as pin 3). For the rate sweep you can use the generator test input instead (1 kHz, 1 Vpp).

- [ ] First ~20 s: six `RATE_TEST,<requested>,<measured>,<overflows>` lines → `python tools/rate_table.py LOG` gives the table (requested vs measured, % error)
  → **sets** `APP_SAMPLE_RATE_ACTUAL_HZ` (measured value at 40 000 requested); decides whether 40 kHz stays
- [ ] Then `RATE / STATS / RAW` every second. Through the preamp, save a separate log of about 10 s each of:
  - [ ] quiet room (nobody talking) → `STATS` mean = bias in counts; rms = noise
  - [ ] talking at ~30 cm
  - [ ] clap at ~30 cm → does `STATS` min/max reach near 0 / 4095 (clipping)?
  - [ ] phone playing 1 kHz tone at ~30 cm
  - Name like `2026-10-30_02_preamp_quiet.txt`
- [ ] → **decides** whether one preamp stage is enough (talking should move RAW by at least ~±50 counts) or a second stage is needed
- [ ] → **sets** `APP_SILENCE_RMS` (a bit above the quiet-room rms)
- [ ] → **checks** `APP_CLIP_MARGIN` (how close to 0/4095 a clap gets)
- [ ] `python tools/plot_raw.py LOG` on each log: bias / min / max / rms summary + plot. The 1 kHz log should look like a sine with one spectrum peak: evidence for the report

---

## Session B — main firmware (code ready; needs A1 orientation + A2 rate values set first)

Wiring = A1 + A2 together. Buttons optional at first (to GND): MODE → GPIO 14, LISTEN → GPIO 21. Without buttons the firmware starts in LOG mode.
At boot the log prints a `config:` line with the settings used — keep it in every evidence log.
Two modes since 05/11, both 32 bars over 100 Hz – 8 kHz with the same FFT: **LOG** (hybrid-log columns, mode 0 in FRAME lines) and **LINEAR** (equal-width columns, mode 3). MODE short press toggles them (saved, logged as `MODE short: mode -> LOG/LINEAR`); MODE long press = next brightness (0, 2, 5, 9, 15, saved). LISTEN short = stop/start (display blanks while stopped); LISTEN long does nothing. The display shows plain bars only; TONE lines and status bits are still logged for the accuracy tests. The orientation is fixed in `APP_ORIENT_*` (A1 probe): at power-up the display shows a staircase for 1.5 s, which must rise from bottom-left to top-right, and logs `ORIENT fixed: R=.. FX=.. FY=.. T=..`. If it doesn't, re-run the A1 probe; no button changes the orientation.

```bash
idf.py build flash -p /dev/ttyACM0 monitor | tee docs/evidence/logs/<date>_<test>.txt
```

### B1. Noise floor — quiet room
- [ ] Mic connected, room quiet, LOG mode, 30 s log (the 30/10 log was taken in bass/voice mode, so redo it for the LM358 preamp: `2026-11-05_B1_quiet_lm358.txt`)
  → `python tools/frames.py LOG` prints a suggested `APP_FLOOR_DB` (loudest column's 95th percentile + 1 dB) → **sets** `APP_FLOOR_DB`; set `APP_TONE_MIN_DB` ~10 dB above it
- [ ] Check R5: ≤ 1 lit pixel per column in silence (photo)

**30/10 result:** the quiet-room log showed peaks at 700 / 1400 / 2100 / 2800 Hz, 25–30 dB above the room. That's the MAX7219 row scan (~700 Hz) coupling into the mic preamp through the shared supply/ground. Fix is in the wiring (see `bringup/README.md`, "Display interference"); re-run B1 after it and compare the two heatmaps: good before/after evidence. `tools/frames.py` now flags such columns instead of using them as the floor.

**05/11 result (LM358):** the lab isn't quiet, so B1 was done with the mic covered. The interference now dominates (≈ 600 Hz, −5.8 dB at brightness 15, −32.8 dB at brightness 0). Accepted as a **known limitation**: brightness default 0, floor −40 dB from the brightness-0 log; columns 11–12 and 28–29 still show ≈ 2 rows in silence. See the PLAN decision log.

### B2. Real frame rate, processing time, latency budget
- [ ] `python tools/frames.py LOG` on any log: frame rate (R4 ≥ 20), processing time, sample rate, display/latency stats, status-flag %
- [ ] `DISPLAY,<fps>,<age_avg_ms>,<age_max_ms>,<write_us>` lines: display refresh (expect ~40), frame age, SPI write time
  → latency budget for the report: capture (25.6 ms at N = 1024) + age_avg ≈ electronic latency; compare with the clap video (B4)
- [ ] Any `ADC buffer overflowed` warnings? If yes → raise `APP_DEBUG_EVERY_N_FRAMES`

### B3. Electrical input path (function generator) — needs a small circuit
Proposed circuit (confirm before building): generator → 10 µF cap → node biased at 1.65 V by two 10 kΩ resistors (3.3 V to GND) → 1 kΩ → GPIO 1, with **2.2 nF** from GPIO 1 to GND. **Preamp output (the 4.7 kΩ lead) unplugged from GPIO 1 while using this.** Generator: sine, **1 Vpp, 0 V offset** (pin sees 1.15–2.15 V).
Why these values: the bias divider looks like 5 kΩ (10 k ∥ 10 k) in series with the 1 kΩ, so the low-pass is set by 6 kΩ × C: 2.2 nF → f_c = 1 / (2π · 6 kΩ · 2.2 nF) ≈ 12 kHz, above the 8 kHz display range and below Nyquist (20 kHz). The 10 µF with 5 kΩ gives a high-pass at ≈ 3 Hz, so no bass is lost. (An earlier draft said 15 nF, which with the 6 kΩ would cut off at ≈ 1.8 kHz — wrong.) A single RC only gives ≈ −5 dB at 20 kHz: enough to *show* the aliasing improvement, not remove it.
**Procedure (06/11)** — firmware with `APP_SAMPLE_RATE_ACTUAL_HZ` 40314 (measured), LOG mode unless stated. One log per tone, about 10 s each:
```bash
tools/capture.sh B3_log_433            # Ctrl+] after ~10 s
python3 tools/tone_stats.py docs/evidence/logs/2026-11-06_B3_log_433.txt --set-hz 433 --path electrical --skip-s 3 --csv docs/evidence/accuracy.csv
```
`tone_stats.py` prints shown Hz, error, level (dBFS) and the **loudest column** — that column is the R2 result. `--skip-s 3` skips the reset + 1.5 s boot staircase.

Tones = the centre of every 4th column at the measured rate (bins 39.37 Hz; from `band_map_build`, same as the boot `columns (Hz):` line):

| Mode | col 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 31 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LOG (Hz) | 118 | 276 | 433 | 728 | 1201 | 1949 | 3209 | 5216 | 7539 |
| LINEAR (Hz) | 217 | 1201 | 2185 | 3169 | 4153 | 5138 | 6142 | 7126 | 7874 |

- [ ] Column accuracy (R2), LOG: all 9 tones above → expect loudest column = the column in the header (±1 passes R2). **06/11: only 1201, 4153, 7874 Hz done in LOG (all correct); the other 8 still to do.** `tone_stats.py` now prints the mode and the expected column, so check its output after each log
- [x] Column accuracy, LINEAR (06/11): all 9 LOG-table tones (118 … 7539 Hz) ran in LINEAR by mistake — 9/9 in the expected LINEAR column; shown Hz within 0.03 % (`accuracy.csv`, `plots/accuracy.png`)
- [ ] Tone accuracy: the same LOG logs give shown-vs-set Hz; then `python3 tools/plot_accuracy.py docs/evidence/accuracy.csv --bin-hz 39.37`
- [ ] Frequency response (R1): 50, 100, 200, 500 Hz, 1, 2, 5, 8, 10, 12, 15 kHz, same amplitude; `level_db` in the CSV vs frequency (expect ≈ flat to 8 kHz, then the 12 kHz RC roll-off)
- [ ] Aliasing (R6): **25, 35, 38 kHz**. Sampling at 40.3 kHz, a tone at f shows up at 40 314 − f: 25 kHz → 15.3 kHz (off the display, should show nothing), 35 kHz → 5.3 kHz (column 28), 38 kHz → 2.3 kHz (column 21). Log each with and without the 2.2 nF cap; `tone_stats.py --set-hz 35000` reports where it appears and how loud. (The 30/10 plan said 25 and 30 kHz: both alias above 8 kHz, so they can't show the problem.)
- [ ] Optional — leakage: 1 kHz with `APP_USE_WINDOW` 1 vs 0 (needs a rebuild); how many neighbouring columns light

### B4. Acoustic path (phone tone app → speaker → mic)
- [ ] Same tone list as B3, phone at fixed distance (note it) — `tone_stats.py … --path acoustic` into the same CSV, so the plot compares both paths
- [ ] Loudness (R7): 1 kHz, phone volume in steps — bar height vs volume. No AGC now, so this should be close to linear in dB until the preamp clips; may set `APP_DB_PER_ROW`
- [ ] Latency (R3): slow-mo phone video of a clap next to the display → frames from clap to LEDs
- [ ] Music + speech demo videos: LOG vs LINEAR (same song or sweep, logs `2026-11-05_R_log.txt` / `_R_linear.txt`; one video pressing MODE mid-sound) — in LINEAR speech crowds into the left few columns, in LOG it spreads across the strip

### B5. Buttons and modes
- [ ] MODE short toggles LOG ↔ LINEAR; MODE long changes brightness; LISTEN short stops/starts (blank display); LISTEN long does nothing — each logged
- [ ] Boot staircase rises bottom-left → top-right after every power-up and reflash, no button presses
- [ ] Mode label (branch `feature/mode-label`): after the staircase the saved mode's name shows for ~1 s; each MODE short press shows the new name (LOG / LINEAR) for ~1 s, then bars; serial shows `label LOG` / `label LINEAR`. Evidence: short video of 3–4 presses + log
- [ ] Power-cycle: mode and brightness survive (R8); always comes back listening
- [ ] Optional: USB power meter, brightness 0 vs 15 (sustainability point)

---

## Values still to measure (from `main/app_config.h`)

| Value | Placeholder | Set by test |
| --- | --- | --- |
| `APP_ORIENT_*` | **set 05/11**: R1 FX0 FY1 T0 | A1 probe (bring-up 01 STEP 3) |
| `APP_MAX7219_CLOCK_HZ` | 1 MHz | A1 (optional) |
| `APP_SAMPLE_RATE_ACTUAL_HZ` | 40 000 | A2 |
| Preamp: one or two stages, RB value | 1 stage, 470 kΩ | A2 |
| `APP_SILENCE_RMS` | 8 | A2 / B1 |
| `APP_CLIP_MARGIN` | 16 | A2 |
| `APP_FLOOR_DB` | **set 05/11**: −40 (`2026-11-05_B1_covered_b0.txt`, mic covered, brightness 0) | B1 |
| `APP_TONE_MIN_DB` | **set 05/11**: −30 (floor + 10 dB) | B1 |
| `APP_FALL_ROWS_PER_S`, `APP_PEAK_*` | 20 / 0.5 s / 6 | B4 videos (tune by eye, note before/after) |
