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
- [ ] STEP 3: number `k` of the clean staircase (rises bottom-left → top-right)
  → **sets** `APP_ORIENT_REVERSE_DEVICES / FLIP_X / FLIP_Y / TRANSPOSE` (copy the four flags from the `ORIENT k` line)
- [ ] Reflash with the flags set (it runs steps 1–3 again first, ~80 s, then STEP 4), soak 5 min: any random pixels? note `write_avg` / `write_max`. The bring-up does **not** re-send control registers, so any glitch stays visible here (the main firmware re-sends them every second)
  → evidence for the 3.3 V-logic risk; `write_avg` goes in the latency budget
- [ ] Optional: soak again at `APP_MAX7219_CLOCK_HZ` = 4 MHz and 10 MHz → **sets** the clock (fastest clean one, or stay at 1 MHz)

### A2. Mic + ADC bring-up — `bringup/02_mic_adc`

```bash
cd bringup/02_mic_adc && idf.py set-target esp32s3   # first time only
idf.py build flash -p /dev/ttyACM0 monitor | tee ../../docs/evidence/logs/2026-10-29_02_rate_sweep.txt
```

Wiring: MAX9814 VDD → 3.3V, GND → GND, OUT → GPIO 1. Gain pin: VDD = 40 dB, GND = 50 dB, open = 60 dB. A/R open.

- [ ] First ~20 s: six `RATE_TEST,<requested>,<measured>,<overflows>` lines → `python tools/rate_table.py LOG` gives the table (requested vs measured, % error)
  → **sets** `APP_SAMPLE_RATE_ACTUAL_HZ` (measured value at 40 000 requested); decides whether 40 kHz stays
- [ ] Then `RATE / STATS / RAW` every second. For **each gain setting (40, 50, 60 dB)** save a separate log of about 10 s each of:
  - [ ] quiet room (nobody talking) → `STATS` mean = bias in counts; rms = noise
  - [ ] talking at ~30 cm
  - [ ] clap at ~30 cm → does `STATS` min/max reach near 0 / 4095 (clipping)?
  - [ ] phone playing 1 kHz tone at ~30 cm
  - Name like `2026-10-29_02_gain40_quiet.txt`
- [ ] → **sets** gain choice (lowest gain that still gives a usable signal for talking; least clipping on claps)
- [ ] → **sets** `APP_SILENCE_RMS` (a bit above the quiet-room rms at the chosen gain)
- [ ] → **checks** `APP_CLIP_MARGIN` (how close to 0/4095 a clap gets)
- [ ] `python tools/plot_raw.py LOG` on each log: bias / min / max / rms summary + plot. The 1 kHz log should look like a sine with one spectrum peak: evidence for the report

---

## Session B — main firmware (code ready; needs A1 orientation + A2 rate values set first)

Wiring = A1 + A2 together. Buttons optional at first (to GND): MODE → GPIO 14, LISTEN → GPIO 21. Without buttons the firmware starts in full mode.
At boot the log prints a `config:` line with the settings used — keep it in every evidence log.
Modes (MODE short press): 0 full → 1 bass/voice → 2 tone finder → 3 linear. MODE long press = brightness. LISTEN = stop/start.

```bash
idf.py build flash -p /dev/ttyACM0 monitor | tee docs/evidence/logs/<date>_<test>.txt
```

### B1. Noise floor — quiet room
- [ ] Mic connected, room quiet, full mode, 30 s log
  → `python tools/frames.py LOG` prints a suggested `APP_FLOOR_DB` (loudest column's 95th percentile + 1 dB) → **sets** `APP_FLOOR_DB`; set `APP_TONE_MIN_DB` ~10 dB above it
- [ ] Check R5: ≤ 1 lit pixel per column in silence (photo)

### B2. Real frame rate, processing time, latency budget
- [ ] `python tools/frames.py LOG` on any log: frame rate (R4 ≥ 20), processing time, sample rate, display/latency stats, status-flag %
- [ ] `DISPLAY,<fps>,<age_avg_ms>,<age_max_ms>,<write_us>` lines: display refresh (expect ~40), frame age, SPI write time
  → latency budget for the report: capture (25.6 ms at N = 1024) + age_avg ≈ electronic latency; compare with the clap video (B4)
- [ ] Any `ADC buffer overflowed` warnings? If yes → raise `APP_DEBUG_EVERY_N_FRAMES`

### B3. Electrical input path (function generator) — needs a small circuit
Proposed circuit (confirm before building): generator → 10 µF cap → node biased at 1.65 V by two 10 kΩ resistors (3.3 V to GND) → 1 kΩ → GPIO 1, with **2.2 nF** from GPIO 1 to GND. **Mic unplugged from GPIO 1 while using this.** Generator: sine, **1 Vpp, 0 V offset** (pin sees 1.15–2.15 V).
Why these values: the bias divider looks like 5 kΩ (10 k ∥ 10 k) in series with the 1 kΩ, so the low-pass is set by 6 kΩ × C: 2.2 nF → f_c = 1 / (2π · 6 kΩ · 2.2 nF) ≈ 12 kHz, above the 8 kHz display range and below Nyquist (20 kHz). The 10 µF with 5 kΩ gives a high-pass at ≈ 3 Hz, so no bass is lost. (An earlier draft said 15 nF, which with the 6 kΩ would cut off at ≈ 1.8 kHz — wrong.) A single RC only gives ≈ −5 dB at 20 kHz: enough to *show* the aliasing improvement, not remove it.
- [ ] Column accuracy (R2): tone at the centre of every 4th column — note which column lights. Use the `columns (Hz):` line the firmware prints at boot and on every mode change (it uses the measured sample rate; the `test_band_map` table assumes exactly 40 kHz)
- [ ] Tone-finder accuracy: 100, 200, 440, 1000, 2000, 5000, 7500 Hz — one log per tone (`capture.sh B3_tone440` …), then `tools/tone_stats.py LOG --set-hz F --path electrical --csv docs/evidence/accuracy.csv` per log, then `tools/plot_accuracy.py docs/evidence/accuracy.csv`
- [ ] Frequency response (R1): 50 Hz → 20 kHz in steps, same amplitude — peak column level vs frequency
- [ ] Leakage: 1 kHz with `APP_USE_WINDOW` 1 vs 0 — how many neighbouring columns light
- [ ] Two-tone resolution (if the generator has two channels, or generator + phone): full vs bass/voice mode
- [ ] Aliasing (R6): 25 kHz and 30 kHz tones — where do they show up? With and without the 15 nF cap

### B4. Acoustic path (phone tone app → speaker → mic)
- [ ] Same tone list as B3, phone at fixed distance (note it) — `tone_stats.py … --path acoustic` into the same CSV, so the plot compares both paths
- [ ] Loudness / AGC (R7): 1 kHz, phone volume in steps — bar height vs volume
- [ ] Latency (R3): slow-mo phone video of a clap next to the display → frames from clap to LEDs
- [ ] Music + speech demo videos: full mode vs linear mode (same song) — the linear vs hybrid comparison

### B5. Buttons and modes
- [ ] Every mode via MODE button; long press changes brightness; LISTEN stops/starts
- [ ] Status pixels (top row, right): col 31 = silent, 30 = clipping, 29 = above range, 28 = not listening — trigger each (quiet room / loud clap / 12 kHz tone / LISTEN button), photo each
- [ ] Tone-finder mode: digits readable? marker pixel under the right column?
- [ ] Power-cycle: mode and brightness survive (R8); always comes back listening
- [ ] Optional: USB power meter, brightness 0 vs 15 (sustainability point)

---

## Values still to measure (from `main/app_config.h`)

| Value | Placeholder | Set by test |
| --- | --- | --- |
| `APP_ORIENT_*` | all false | A1 |
| `APP_MAX7219_CLOCK_HZ` | 1 MHz | A1 (optional) |
| `APP_SAMPLE_RATE_ACTUAL_HZ` | 40 000 | A2 |
| Mic gain pin | — (wiring) | A2 |
| `APP_SILENCE_RMS` | 8 | A2 / B1 |
| `APP_CLIP_MARGIN` | 16 | A2 |
| `APP_FLOOR_DB` | −60 | B1 |
| `APP_TONE_MIN_DB` | −50 | B1 |
| `APP_FALL_ROWS_PER_S`, `APP_PEAK_*` | 20 / 0.5 s / 6 | B4 videos (tune by eye, note before/after) |
