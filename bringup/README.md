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
3. **STEP 3** — staircase shown in 16 orientations, 4 s each, each logged as `ORIENT k: REVERSE_DEVICES=… FLIP_X=… FLIP_Y=… TRANSPOSE=…`. The right one is a clean staircase rising from bottom-left (1 pixel) to top-right (8 pixels) in steps of 4 columns, with the input connector on the side you want as "left". If two look right, pick the one where the module's DIN is on the left.
4. **STEP 4** — staircase with the `APP_ORIENT_*` values from `main/app_config.h`, rewritten 40×/s. A `SOAK …` line every 10 s gives write time (avg/max). After setting the flags, reflash and let it run 5 min.

Record:

- [ ] Photo: test mode (all on)
- [ ] Photos of STEP 2 A, B, C (which chip is chip 0, which corner is row 0 / bit 7)
- [ ] The `ORIENT k` number that looks right → copy its four flags into `APP_ORIENT_*` in `main/app_config.h`
- [ ] Staircase photo, left = column 0
- [ ] Log of the 5-minute soak (`write_avg` / `write_max`); any random pixels? (3.3 V logic into a 5 V chip — if yes, plan the 74HCT125 buffer)
- [ ] Optional: repeat the soak at `APP_MAX7219_CLOCK_HZ` = 4 MHz and 10 MHz; note the fastest that stays clean

## 02 — Mic preamp → ADC (`02_mic_adc/`)

Needs: `components/adc_sampler` written first. Schematic: `docs/diagrams/circuit.png` (top-left box).

The MAX9814 never arrived, so the mic is a bare electret capsule with a one-NPN preamp (common emitter, collector feedback):

| Part | Value | Connects |
| --- | --- | --- |
| R0 | 220 Ω | 3V3 → filtered rail (with C0) |
| C0 | 100 µF electrolytic | filtered rail → GND (+ to the rail) |
| R1 | 2.2 kΩ | filtered rail → capsule + (powers the capsule) |
| Capsule | electret | + to R1/C1, − (pin tied to the metal case) to GND |
| C1 | 1 µF | capsule + → Q1 base |
| Q1 | NPN, BC547 / 2N3904 | emitter → GND; **check the pinout for your part** |
| RB | 470 kΩ | Q1 collector → Q1 base (sets the bias) |
| RC | 4.7 kΩ | filtered rail → Q1 collector |
| C2 | 2.2 nF | Q1 collector → GND (anti-aliasing with RC, ≈ 15 kHz) |
| Output | — | Q1 collector → GPIO 1 |

Before running: with the mic connected and the room quiet, measure the collector with a multimeter. Expect **1.1–1.9 V**. Too low → RB 680 kΩ; too high → RB 330 kΩ. Record the value.

Expected: `RATE,…` once a second near the requested rate; `RAW,…` values centred on the collector voltage (≈ 1500–2400 counts).

Record:

- [ ] Requested vs measured sample rate (try 3–4 rates, note where it stops keeping up)
- [ ] Collector voltage (multimeter) and the transistor part number
- [ ] Raw logs: quiet room / talking / clap / phone 1 kHz tone (phone at a noted distance)
- [ ] Mean value in silence (the bias in raw counts) and where clipping starts
- [ ] If talking barely moves the RAW values, note it: that's the case for a second gain stage
- [ ] Plot one 1 kHz frame in Python — does it look like a sine wave?
