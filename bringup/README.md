# Bring-up tests

Small standalone ESP-IDF projects, one per part, run before the main firmware.
Each uses the real component from `components/`, so a bring-up also tests that driver.

Build and run one (from the repo root):

```bash
cd bringup/01_matrix
idf.py set-target esp32s3        # first time only
idf.py build flash -p /dev/ttyACM0 monitor
# Ctrl+] to leave the monitor
```

Save a log as evidence:

```bash
idf.py -p /dev/ttyACM0 monitor | tee ../../docs/evidence/logs/02_quiet_room.txt
```

**Before anything:** unplug the camera ribbon on the Freenove board (the camera uses GPIO 4–13 and 15–18).

---

## 01 — MAX7219 matrix (`01_matrix/`)

Needs: `components/max7219` and the drawing parts of `components/frame_gfx` written first.

| Module pin | Connect to |
| --- | --- |
| VCC | 5 V |
| GND | GND |
| DIN | GPIO 11 |
| CS | GPIO 10 |
| CLK | GPIO 12 |

Expected (serial log says which step is running):

1. **STEP 1** — all LEDs on for 3 s (hardware test mode).
2. **STEP 2** — three single LEDs, 4 s each: **A** = chip 0 row-register 0 bit 7, **B** = same register bit 0, **C** = row-register 7 bit 7. Chip 0 is the one nearest the DIN pin.
3. **STEP 3 — orientation probe.** Raw register writes, no `frame_gfx`. Four single LEDs are added one at a time, 5 s each, and the sequence runs 3 times (1 min) before STEP 4. Hold the strip exactly as it will sit in the demo; "left/right/up/down" mean as you look at it.

   | Step | Lit (cumulative) | Log line |
   | --- | --- | --- |
   | P1 | chip 0, reg 0, bit 0 — the **origin O** | `PROBE P1 origin: dev0 reg0 bit0` |
   | P2 | + chip 0, reg 0, bit 7 | `PROBE P2: + dev0 reg0 bit7 (which way from O?)` |
   | P3 | + chip 0, reg 7, bit 0 | `PROBE P3: + dev0 reg7 bit0 (which way from O?)` |
   | P4 | + chip 1, reg 0, bit 0 | `PROBE P4: + dev1 reg0 bit0 (which module?)` |

   Note four things: where P2 is from O, where P3 is from O, which module (1–4 from the left) O is in, and which module P4 is in. Then set the flags in `main/app_config.h`:

   | You see | Set |
   | --- | --- |
   | P2 is **left or right** of O (same row) | `TRANSPOSE = false` |
   | P2 is **above or below** O (same column) | `TRANSPOSE = true` |
   | TRANSPOSE false: P2 **left** of O / **right** of O | `FLIP_X = false` / `true` |
   | TRANSPOSE false: P3 **above** O / **below** O | `FLIP_Y = false` / `true` |
   | TRANSPOSE true: P2 **above** O / **below** O | `FLIP_Y = false` / `true` |
   | TRANSPOSE true: P3 **right** of O / **left** of O | `FLIP_X = false` / `true` |
   | O is in the **leftmost** module / the **rightmost** module | `REVERSE_DEVICES = false` / `true` |

   Sanity checks — if either fails, stop: the chain or the driver's device order is not what `frame_to_device_rows()` assumes.
   - P2 and P3 are at right angles to each other, and each is 7 LEDs from O (opposite corners of one module's edges).
   - P4 is in the module next to O's.

   Why the table is right: in `frame_to_device_rows()`, without transpose `reg = y'` and `bit = 7 − x'`, so bit 7 is x' = 0 (left) and reg 7 is y' = 7 (top); with transpose `reg = x'` and `bit = y'`, so bit 7 is y' = 7 (top) and reg 7 is x' = 7 (right) (x', y' = frame coordinates after the flips). `host_tests/test_frame_gfx.c` checks the table against the code for all 16 flag sets.
4. **STEP 4** — staircase with the `APP_ORIENT_*` values from `main/app_config.h`, rewritten 40×/s. A `SOAK …` line every 10 s gives write time (avg/max). After setting the flags, reflash and let it run 5 min.

Record:

- [ ] Photo: test mode (all on)
- [ ] Photos of STEP 2 A, B, C (which chip is chip 0, which corner is row 0 / bit 7)
- [ ] Probe answers (P2 and P3 direction from O, module of O and P4) → the four `APP_ORIENT_*` flags from the table above
- [ ] Photos of the probe at P3 (O, P2, P3 lit) and P4: `docs/evidence/photos/<date>_A1_probe_P3.jpg`, `..._P4.jpg`
- [ ] Staircase photo, left = column 0
- [ ] Log of the 5-minute soak (`write_avg` / `write_max`); any random pixels? (3.3 V logic into a 5 V chip — if yes, plan the 74HCT125 buffer)
- [ ] Optional: repeat the soak at `APP_MAX7219_CLOCK_HZ` = 4 MHz and 10 MHz; note the fastest that stays clean

## 02 — Mic preamp → ADC (`02_mic_adc/`)

Needs: `components/adc_sampler` written first. Schematics: `docs/diagrams/preamp-1.png` (one stage, build this first) and `preamp-2.png` (two stages). Each sheet has the DC readings to check and the chip pins.

The MAX9814 never arrived, so the mic is a bare electret capsule. The first one-NPN preamp gave too little response; it is now an **LM358** (dual op-amp) on the filtered 3.3 V rail, as non-inverting stages:

| Part | Value | Connects |
| --- | --- | --- |
| R0 | 220 Ω | board 3V3 → filtered rail (with C0) |
| C0 | 100 µF electrolytic | filtered rail → GND (+ to the rail) |
| R1 | 2.2 kΩ | filtered rail → capsule + (powers the capsule) |
| Capsule | electret | + to R1/C1, − (pin tied to the metal case) to GND |
| C1 | 1 µF | capsule + → pin 3 (+ side to the mic if electrolytic) |
| Bias | 220 kΩ + 100 kΩ | rail → pin 3 → GND: holds the input at ≈ 0.95 V |
| LM358 supply | pin 8 / pin 4 | filtered rail / GND, 100 nF straight across 8–4 |
| Rf | 100 kΩ | pin 1 → pin 2 |
| Gain leg | 1 kΩ then 10 µF | pin 2 → GND (10 µF + to the 1 kΩ): AC gain ×101, DC gain 1 |
| Output filter | 4.7 kΩ, 2.2 nF | pin 1 → 4.7 kΩ → GPIO 1; 2.2 nF GPIO 1 → GND (≈ 15 kHz) |
| Half B (one stage) | — | pin 7 → pin 6, pin 5 → GND |
| Half B (two stages) | C3 1 µF, 220 k/100 k, Rf 10 kΩ, 1 kΩ + 10 µF | pin 1 → C3 → pin 5 (own bias); gain ×11; output from pin 7 instead |

Why the LM358 on 3.3 V, not 5 V: on 3.3 V its output can't rise above ≈ 1.8 V, so it can never over-drive GPIO 1.

Before running: room quiet, measure pin 1 (and pin 7 for two stages). Expect **0.9–1.1 V**, the same as pin 3. Record it.

Expected: `RATE,…` once a second near the requested rate; `RAW,…` values centred on the op-amp output (≈ 1.0 V ≈ 1300 counts).

Record:

- [ ] Requested vs measured sample rate (try 3–4 rates, note where it stops keeping up)
- [ ] Pin 1 / pin 7 DC voltage (multimeter), one or two stages
- [ ] Raw logs: quiet room / talking / clap / phone 1 kHz tone (phone at a noted distance)
- [ ] Mean value in silence (the bias in raw counts) and where clipping starts
- [ ] If talking barely moves the RAW values, note it: that's the case for a second gain stage
- [ ] Plot one 1 kHz frame in Python — does it look like a sine wave?

### Display interference (found 30/10)

With the display running, a quiet-room log showed tones at **≈700 Hz and its harmonics** (1400, 2100, 2800 Hz), 25–30 dB above the room noise. The MAX7219 scans its 8 LED rows ~700 times a second and switches up to a few hundred mA each time; that current pulse shares the 5 V / GND wires with the mic preamp and shows up as a "tone".

Fixes, in order of effort:

1. **Separate ground returns:** run the display's GND straight to an ESP32 GND pin with its own wire, and the preamp's GND to a *different* GND pin. Don't let display current flow through the breadboard rail the mic uses.
2. **Decouple the display at the module:** 100 µF electrolytic + 100 nF ceramic across the module's VCC and GND pins, as close to the header as possible.
3. **Keep the preamp rail filter** (R0 220 Ω + C0 100 µF) close to the preamp, and keep mic wires short and away from the display cable.
4. **Lower the brightness** (MODE long press): less LED current, smaller pulses. Note the level before/after as evidence.

**Measured 05/11 (LM358 ×101, mic covered, LOG mode)**, logs `2026-11-05_B1_covered_b15.txt` / `_b0.txt`: at brightness 15 the worst columns (10–11, ≈ 600 Hz) read −5.8 dB p95 and 7 % of frames clip; at brightness 0 the worst column is −32.8 dB, the typical column drops from −29.9 to −42.6 dB and nothing clips. A ≈ 27 dB drop from LED current alone, while the SPI data is the same at both levels, so the coupling is through the supply/ground current pulses, not the data wires. Fixes 1–2 are the real cure; brightness 0 is the stop-gap.

**Decision 05/11:** fixes 1–3 not attempted (time); the interference is a known limitation, mitigated by fix 4 (brightness default 0). See the PLAN decision log.

Check: quiet-room log with `tools/frames.py` — the WARNING line about interference columns should disappear, or the listed columns drop towards the rest.
