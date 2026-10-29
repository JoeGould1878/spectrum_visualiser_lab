# CLAUDE.md

Guidance for Claude when working in this repository.

## Project

Audio-reactive spectrum visualiser (Mini-Challenge 2, CDIO) — ESP32-S3 + MAX9814 mic + 32×8 MAX7219, ESP-IDF v6, C.
The assessment is on the **engineering process and evidence**, not the product. Read `docs/CONTEXT.md` first, then `docs/PLAN.md`.

## How we work

- **Speed matters: Claude writes the implementation.** Implement against the existing headers (they are the contract); change a header only when there's a real reason, and say so.
- Work component by component in the order in `docs/CONTEXT.md` (bring-ups first). Build after every change (`idf.py build`, `cd host_tests && make`) and fix errors before handing over.
- Joe flashes and tests on the hardware; give him the exact commands and say what output to expect and what to record as evidence.
- Keep the process evidence alive even when moving fast: every tunable number marked MEASURE gets set from a test, and every non-obvious choice gets a line in the decision log in `docs/PLAN.md`.
- **Keep Joe in the loop.** After each chunk of work, give a short summary: what was written, each design choice made and why, and what he needs to do next on the hardware. He has to explain the system in the demo, so name the important decisions plainly.
- **Ask Joe first** before changing team decisions in `docs/PLAN.md` (requirements, framing, features) or the wiring.
- Commit messages say what changed and why — the git history is part of the evidence.
- After each step, update `docs/CONTEXT.md` (date, what was done, decisions, next step).

## Commands

```bash
. $IDF_PATH/export.sh
idf.py set-target esp32s3                 # once per project dir
idf.py build
idf.py build flash -p /dev/ttyACM0 monitor  # Ctrl+] to exit
idf.py -p /dev/ttyACM0 monitor | tee docs/evidence/logs/<name>.txt
cd host_tests && make                     # laptop tests for pure-C components
cd bringup/01_matrix && idf.py build      # bring-ups are separate IDF projects
```

Environment: Debian 13, ESP-IDF v6, VS Code. Board enumerates as `/dev/ttyACM0`.

## Architecture rules

- Signal path: `adc_sampler → spectrum → band_map → tone_finder → bar_model → frame_gfx → max7219`.
- `components/` never include anything from `main/`.
- **Pure-C components** (`band_map`, `bar_model`, `tone_finder`, `frame_gfx`) include only the C standard library, so `host_tests/` can build them with plain gcc. Keep it that way.
- Ownership: only `audio_task` touches `adc_sampler`/`spectrum`/`band_map`; only `display_task` touches `max7219`/`bar_model`; only `input_task` touches `button`.
- Every pin, rate and threshold lives in `main/app_config.h`. Values marked MEASURE are placeholders until a test sets them.
- `frame_to_device_rows()` is the only place that knows how the matrix is mounted.
- Serial debug lines follow the formats in `main/debug_stream.h` (parsed by `tools/`).

## Conventions

- C11, ESP-IDF style; public functions return `esp_err_t` where they can fail; `ESP_LOGx` with a `TAG` for human logs, `debug_stream` for machine-readable lines.
- Each `.c` file header names the author and credits any source adapted (brief requirement).
- Evidence (logs, photos, plots, videos) goes in `docs/evidence/` with dated names.

## Hardware notes

- Freenove ESP32-S3: unplug the camera (uses GPIO 4–13, 15–18). Avoid GPIO 2 (LED), 0/3/45/46 (strapping), 19/20 (USB), 35–37 (PSRAM).
- ADC continuous mode: ADC1 pins only (GPIO 1–10); check the rate limit in `soc/soc_caps.h`.
- MAX9814 has its own AGC — don't add software auto-gain.
- MAX7219 at 5 V with 3.3 V logic is below spec; watch for random pixels.
