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

Expected: all LEDs on in test mode → then single pixel → arrow → staircase.

Record:

- [ ] Photo: test mode (all on)
- [ ] Which chip is chip 0, and which corner is its row 0 / bit 0
- [ ] The `frame_orient_t` settings that make the arrow point at column 0 → copy into `main/app_config.h`
- [ ] Staircase photo, left = column 0
- [ ] 5-minute run: any random pixels? (3.3 V logic into a 5 V chip — if yes, plan the 74HCT125 buffer)

## 02 — MAX9814 mic → ADC (`02_mic_adc/`)

Needs: `components/adc_sampler` written first.

| MAX9814 pin | Connect to |
| --- | --- |
| VDD | 3.3 V (keeps the output inside the ADC range) |
| GND | GND |
| OUT | GPIO 1 (ADC1) |
| Gain | open = 60 dB, GND = 50 dB, VDD = 40 dB |
| A/R | open (default 1:4000) |

Expected: `RATE,…` once a second near the requested rate; `RAW,…` values centred around the 1.25 V bias.

Record:

- [ ] Requested vs measured sample rate (try 3–4 rates, note where it stops keeping up)
- [ ] Raw logs: quiet room / talking / clap / phone 1 kHz tone, at each gain setting
- [ ] Mean value in silence (the bias in raw counts) and where clipping starts
- [ ] Plot one 1 kHz frame in Python — does it look like a sine wave?
