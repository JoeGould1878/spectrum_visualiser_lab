# Spectrum visualiser — running context

Kept by Claude so any new chat or Claude Code session can pick up where we left off. Updated after each step.
**Last updated:** Thu 5 Nov 2026

## How we work

- **Fast mode:** Claude writes the implementation against the existing headers; Joe flashes, tests on hardware and records evidence. (Different from the hourglass, where Joe wrote the code.)
- Build must pass before each handover; Joe reports serial output/photos back.
- Joe stays in the loop: after each chunk, a short summary of what was written, the decisions made and why, and the next hardware step. Team decisions (requirements, features, wiring) are checked with him first.

## Where things are

- Repo: `~/esp/s1_labs/spectrum_visualiser` (git) → GitHub: https://github.com/JoeGould1878/spectrum_visualiser_lab
- Lab test checklist (what to run, record, and which config value each test sets): `docs/LAB_TESTS.md`
- Plan (Conceive + Design, requirements, tests, sessions, decision log): `docs/PLAN.md`; live doc https://claude.ai/artifact/BAJq52LbSn5nmyxJky5Ten
- Brief: `docs/brief/MiniChallenge2-SpectrumVisualiser.pdf`
- Environment: Debian 13, ESP-IDF v6, VS Code; board on `/dev/ttyACM0`

## Hardware

- **Freenove ESP32-S3-WROOM** (same board as the hourglass) — camera unplugged
- **Mic: bare electret capsule + one-NPN preamp** (MAX9814 not available). Common emitter with collector feedback, gain ≈ ×35–50, output ≈ 1.5 V DC + audio, no AGC. Parts table: `bringup/README.md`; schematic: `docs/diagrams/circuit.png`
- **4-in-1 MAX7219** 32 × 8 matrix at 5 V
- 2 push buttons (mode, listen)

| Signal | GPIO |
| --- | --- |
| Mic preamp out / generator test input (ADC1 ch0) | 1 |
| MAX7219 DIN / CLK / CS | 11 / 12 / 10 |
| Button mode / listen | 14 / 21 |

## Background (from previous students)

- Course repo (github.com/caseyov/spectrumVisualiser) is private → firmware written from scratch.
- Aidan (classic ESP32): `analogRead` gave ~12 kHz instead of 60 kHz → I2S-ADC + DMA at ~96 kHz, N = 512 (187.5 Hz bins), 4 linear ranges on a button, tested by eye with a signal generator; mic never arrived.
- Zhexi (via Casey): ~24 kHz continuous ADC, foldback (aliasing) above 12 kHz, analogue low-pass helped but not fully.

## Decided

- ESP-IDF v6, from scratch (29/10)
- Teaching-lab "honest display" framing, accuracy over looks (Joe, 29/10)
- Lab function generator available → two input paths (generator + mic) (29/10)
- Proposed (to confirm with evidence): hybrid log mapping; no software AGC; tone-finder flagship

## Progress

- [x] Brief + resources read; plan written (`docs/PLAN.md`)
- [x] Repo skeleton: headers, CMake files, empty `.c` stubs, bring-up projects, host-test stubs (29/10). Claude built it with ESP-IDF v6.0.3: main project + both bring-ups compile with no warnings; `host_tests` make passes. (esp-dsp was taken from GitHub for that check because the component registry was blocked there — Joe's first build will download it from the registry and create `dependencies.lock`; commit that file.)
- [x] Push to GitHub
- [x] Bring-up 01 code: `max7219` driver, all of `frame_gfx` (+ host tests), bring-up program (29/10). Builds clean.
- [x] Bring-up 01 probe on hardware (05/11): orientation R1 FX0 FY1 T0, fixed in `app_config.h`. Soak at the new flags still to do
- [x] Bring-up 02 code: `adc_sampler` + rate sweep / raw stream (29/10, `81c16af`). Builds clean.
- [ ] Bring-up 02 on hardware: rate sweep, raw logs at each gain
- [x] Pure components + laptop tests: `band_map`, `bar_model`, `tone_finder` (29/10, `fdee253`)
- [x] `spectrum` (esp-dsp): DC removal, decimation filter, Hann, dBFS (29/10, `f92bcea`). Not testable off-board.
- [x] Main app: plumbing (`a8ac360`), audio_task (`517849f`), display_task (`a143fb9`), input_task + main — full firmware builds (29/10)
- [x] Python tools for evidence (`tools/`, checked on synthetic logs) (29/10)
- [x] Display simplified (05/11, spec `docs/specs/2026-11-05_display_simplify.md`): two modes LOG/LINEAR, fixed orientation, bars only
- [ ] Core features → flagship → test plan → demo

## Open questions

- 3.5 mm jack in the box, or mic only?
- Flagship choice; team split
- S3 continuous-ADC maximum rate (check `soc_caps.h`, then measure)

## Log

- **29 Oct:** Plan written from brief + Aidan/Casey blogs. Hardware confirmed. Repo private → ESP-IDF from scratch. Skeleton created. Joe chose to have Claude write the implementation for speed, with summaries after each step.
- **29 Oct:** Joe confirmed teaching-lab framing and that a lab function generator is available. Wrote `max7219` driver (SPI mode 0, no DMA, whole chain per transaction, 1 MHz), all of `frame_gfx` incl. 3x5 font and 16-way orientation mapping (host-tested), and bring-up 01 (test mode → raw bits → orientation sweep → 5-min soak at 40 fps with write timing). Next: Joe runs bring-up 01; meanwhile Claude starts `adc_sampler` / bring-up 02.
- **29 Oct (afternoon):** While Joe on break: adc_sampler + bring-up 02, pure components + tests, spectrum — committed one feature at a time with a review each (Joe asked for per-feature commits + reviews). All decisions logged in PLAN.md. Flagged: linear baseline uses N = 1024 / same range as full mode instead of Aidan's N = 512 (check with team).
- **29 Oct:** Joe confirmed: start listening at power-up; linear baseline at N = 1024 / full range. Added `docs/LAB_TESTS.md` (kept updated per commit).
- **29 Oct:** Credit wording applied to every file (Joe: design/interfaces drafted with Claude; Claude: implementation; Joe: review + hardware testing). Python tools written and checked against synthetic logs. Everything for the 2 pm lab is in `docs/LAB_TESTS.md`.
- **29 Oct:** Full code review before the 2 pm lab. Fixed: tone-finder edge case (+ test), display stale-frame blanking, MAX7219 control-register resync, task stacks, ADC error back-off, column-edge boot log; corrected the electrical-path filter capacitor (15 nF → 2.2 nF) and the flush_pool description. All in the decision log.
- **30 Oct:** Mic kit turned out to be a bare electret capsule, no MAX9814, and no op-amp available. Designed a one-NPN preamp (collector-feedback bias, RB 470 kΩ, RC 4.7 kΩ, gain ≈ ×35–50, 2.2 nF anti-alias) and a 220 Ω + 100 µF rail filter; bias point checked for β 100–400 (collector 1.1–1.9 V). No firmware change needed. Updated wiring diagram, bring-up/lab docs, decision log. Order for the lab: bring-up 01 → bring-up 02 (generator for the rate sweep, then preamp) → main firmware B3 with the generator.
- **30 Oct (pm):** First main-firmware run: display rotated (bars ran along the strip: orientation flags never set) and almost no response to sound. The quiet-room log showed why: peaks at 700/1400/2100/2800 Hz, 25–30 dB above the room = MAX7219 row-scan interference; `frames.py` took the loudest column as the floor (−21 dB), so nothing real could light a row. Fixed: orientation selectable on the board (LISTEN long press, 16 options, test staircase, saved in NVS; default transpose); floor −46 dB / 3 dB per row / tone threshold −36 dB from the room's typical column; `frames.py` now uses the typical column and warns about interference columns. Interference itself needs wiring changes (separate GND returns, decoupling at the display) — listed in `bringup/README.md`. Next: Joe flashes, sets orientation, re-runs B1 after the wiring fix.
- **30 Oct (late):** Joe's bench run (log: orientation 9 saved, board had been left in mode 2) showed tone-finder digits and status pixels, which read as garbage. At Joe's request the display now shows plain bars only (`APP_SHOW_TONE_MODE/STATUS_PIXELS/PEAK_DOTS` = 0, no boot staircase); MODE cycles full → bass/voice → linear; a saved tone-finder mode loads as full. Serial output unchanged. Joe's spare amp board looks like a mono speaker amp (NS8002-type, BTL output) — not suitable as a mic preamp; staying with the S8050 stage.
- **5 Nov:** Preamp changed to an LM358 (NPN stage too weak). New schematics `docs/diagrams/preamp-1.png` (×101) and `preamp-2.png` (×1100), each with DC check values and chip pins; system wiring, hardware diagrams and bringup/README parts table updated. Added a software flowchart (`fw-flow.png`); fw-detail updated to the plain-bars display. Joe is rebuilding the preamp neatly to rule out wiring faults. Next: DC check (pin 1 ≈ 0.95 V), new quiet-room log → re-set `APP_FLOOR_DB`, confirm orientation k for the default.
- **5 Nov (later):** LM358 preamp works and responds to sound. The display is still confusing: 16 orientations on LISTEN, a wrong one saved in NVS, and the bass/linear modes look random. Wrote `docs/specs/2026-11-05_display_simplify.md` for Claude Code: two modes (LOG and LINEAR, MODE short press; brightness on long press), orientation found with a raw-register probe and fixed at compile time, LISTEN = stop/start, NVS mode + brightness. Next: Claude Code does T1 (probe), Joe runs it, then T2–T8.
- **5 Nov (T1 done):** Bring-up 01 step 3 is now a 4-LED raw-register probe (P1 origin dev0/reg0/bit0, P2 +bit7, P3 +reg7, P4 +dev1; 5 s each, 3 rounds, then the soak). Answer → flags table and sanity checks in `bringup/README.md`; new host test checks the table against `frame_to_device_rows()` for all 16 flag sets. Next: Joe runs the probe and reports the four answers → T2; meanwhile T3–T6.
- **5 Nov (T2–T7 done):** Probe answers (wire end = right): O top-right of the rightmost module, P2 left of O, P3 below O, P4 next module left → `REVERSE_DEVICES` 1, `FLIP_X` 0, `FLIP_Y` 1, `TRANSPOSE` 0 (fixed in `app_config.h`, no button/NVS). Firmware now has two modes, LOG (0) and LINEAR (3), same FFT and range; MODE short toggles, MODE long = brightness, LISTEN short = stop/start, LISTEN long = nothing. NVS namespace `sv2` (mode + brightness). Bars only; bass/voice + tone-finder display removed from `main/`. 1.5 s boot staircase. PLAN decision log, LAB_TESTS, README, CLAUDE.md and diagrams (fw-flow, fw-detail, circuit) updated. Found: the 30/10 quiet-room log that set `APP_FLOOR_DB` was in bass/voice mode with the old NPN preamp, so B1 must be redone. Next: Joe flashes the main firmware, checks the boot staircase and buttons, then B1 quiet-room log → `APP_FLOOR_DB`, then the LOG vs LINEAR logs/video.
- **5 Nov (first run, new firmware):** Joe: "miles better". Log `2026-11-05_first_run.txt`: boot `ORIENT fixed: R=1 FX=0 FY=1 T=0`; MODE short toggles LOG↔LINEAR (column map rebuilt each time), MODE long steps brightness 2→5→9→15, LISTEN off/on — all logged (B5 evidence). 38.9 analysed frames/s (R4), frame age 14.7 ms avg / 27.3 ms max, display 40 fps, SPI write ≤ 674 µs, measured sample rate 40 182 Hz. Clipping flag on 13 % of frames (loud sounds clip the ×101 preamp — check in B4). Next (lab): B1 quiet-room log → `APP_FLOOR_DB`; LOG vs LINEAR logs + video; bring-up 01 soak; then B3/B4 accuracy tests.
- **5 Nov (B1, mic covered):** Log `2026-11-05_B1_Floor_covered.txt` (brightness 15, LOG). With the mic covered, columns 10–11 (527–684 Hz) read −5.5 dB p95 and the strongest tone is ≈ 600 Hz (+ 1200 Hz) in nearly every frame; clipping flag 10 %. That's display interference (MAX7219 row scan) amplified by the ×101 LM358, not sound: it now dominates the signal. `frames.py` suggested −26 dB but **`APP_FLOOR_DB` not changed**: a floor that high would hide real sound to mask a wiring fault (see 30/10 decision). The scan is ≈ 600 Hz on this module, not the ≈ 700 Hz noted on 30/10. `logparse.py` fixed to keep only the last boot in a log (monitor reset left old lines first → negative duration). Next: brightness 0 vs 15 covered logs (does the peak follow LED current?), then the wiring fixes in `bringup/README.md`, then redo B1.
