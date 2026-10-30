# Spectrum visualiser — running context

Kept by Claude so any new chat or Claude Code session can pick up where we left off. Updated after each step.
**Last updated:** Thu 29 Oct 2026 (bring-up 01 code)

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
- [ ] Bring-up 01 on hardware (optional now: orientation can be set with LISTEN long press on the main firmware)
- [x] Bring-up 02 code: `adc_sampler` + rate sweep / raw stream (29/10, `81c16af`). Builds clean.
- [ ] Bring-up 02 on hardware: rate sweep, raw logs at each gain
- [x] Pure components + laptop tests: `band_map`, `bar_model`, `tone_finder` (29/10, `fdee253`)
- [x] `spectrum` (esp-dsp): DC removal, decimation filter, Hann, dBFS (29/10, `f92bcea`). Not testable off-board.
- [x] Main app: plumbing (`a8ac360`), audio_task (`517849f`), display_task (`a143fb9`), input_task + main — full firmware builds (29/10)
- [x] Python tools for evidence (`tools/`, checked on synthetic logs) (29/10)
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
