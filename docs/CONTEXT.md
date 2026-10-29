# Spectrum visualiser — running context

Kept by Claude so any new chat or Claude Code session can pick up where we left off. Updated after each step.
**Last updated:** Thu 29 Oct 2026 (bring-up 01 code)

## How we work

- **Fast mode:** Claude writes the implementation against the existing headers; Joe flashes, tests on hardware and records evidence. (Different from the hourglass, where Joe wrote the code.)
- Build must pass before each handover; Joe reports serial output/photos back.
- Joe stays in the loop: after each chunk, a short summary of what was written, the decisions made and why, and the next hardware step. Team decisions (requirements, features, wiring) are checked with him first.

## Where things are

- Repo: `~/esp/s1_labs/spectrum_visualiser` (git) → GitHub: https://github.com/JoeGould1878/spectrum_visualiser_lab
- Plan (Conceive + Design, requirements, tests, sessions, decision log): `docs/PLAN.md`; live doc https://claude.ai/artifact/BAJq52LbSn5nmyxJky5Ten
- Brief: `docs/brief/MiniChallenge2-SpectrumVisualiser.pdf`
- Environment: Debian 13, ESP-IDF v6, VS Code; board on `/dev/ttyACM0`

## Hardware

- **Freenove ESP32-S3-WROOM** (same board as the hourglass) — camera unplugged
- **MAX9814** mic module: AGC, ~1.25 V bias, ~2 Vpp max, gain pin open/GND/VDD = 60/50/40 dB, powered at 3.3 V
- **4-in-1 MAX7219** 32 × 8 matrix at 5 V
- 2 push buttons (mode, listen)

| Signal | GPIO |
| --- | --- |
| Mic OUT (ADC1 ch0) | 1 |
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
- [ ] Bring-up 01 on hardware: Joe flashes, records orientation + soak result ← **NEXT**
- [ ] Bring-up 02 — mic + ADC: write `adc_sampler`, measure real sample rate, raw logs at each gain
- [ ] Pure components on laptop: `band_map`, `bar_model`, `tone_finder`, `frame_gfx` + host tests
- [ ] `spectrum` (esp-dsp) → baseline (Aidan-style linear, N = 512)
- [ ] Core features → flagship → test plan → demo

## Open questions

- 3.5 mm jack in the box, or mic only?
- Flagship choice; team split
- S3 continuous-ADC maximum rate (check `soc_caps.h`, then measure)

## Log

- **29 Oct:** Plan written from brief + Aidan/Casey blogs. Hardware confirmed. Repo private → ESP-IDF from scratch. Skeleton created. Joe chose to have Claude write the implementation for speed, with summaries after each step.
- **29 Oct:** Joe confirmed teaching-lab framing and that a lab function generator is available. Wrote `max7219` driver (SPI mode 0, no DMA, whole chain per transaction, 1 MHz), all of `frame_gfx` incl. 3x5 font and 16-way orientation mapping (host-tested), and bring-up 01 (test mode → raw bits → orientation sweep → 5-min soak at 40 fps with write timing). Next: Joe runs bring-up 01; meanwhile Claude starts `adc_sampler` / bring-up 02.
