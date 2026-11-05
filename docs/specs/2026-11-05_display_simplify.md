# Spec: simplify the display (two modes, LOG and LINEAR, fixed horizontal orientation)

**For:** Claude Code, working in this repo. **Written by:** Claude (planner), 5 Nov 2026, at Joe's request.
**Status:** scope agreed with Joe on 5 Nov ("simplify it"). Joe asked for this change himself, so it counts as his go-ahead under CLAUDE.md's "ask Joe first" rule. Add the decision-log rows from §3 to `docs/PLAN.md` as you implement.

Read `CLAUDE.md`, `docs/CONTEXT.md` and this file. Do the tasks in order; T1 needs Joe at the hardware, so do T1 first and carry on with T3–T7 while he runs it.

---

## 1. Problem (Joe's bench run, 5 Nov, LM358 preamp in)

- **Sound response is now good.** The preamp change worked.
- **The picture is still wrong.** Photos from 5 Nov show lines running *across* each 8 × 8 module, not bars rising along the 32-column strip. The strip sits horizontally with the input header on the right.
- **Too many settings to get lost in:**
  - LISTEN long press steps through 16 orientations, and only one or two look right. Some of the others "work with sound" but look vertical.
  - The saved orientation in NVS survives reflashing, so a wrong one keeps coming back.
  - MODE cycles full / bass-voice / linear. Bass-voice and linear look like "random stuff" to a viewer because the column map changes each time.

**Goal:** the same horizontal picture after every power-up: 32 bars, low notes on the left, bars rising from the bottom edge. **Two modes only** (Joe, 5 Nov): a **log** frequency axis and a **linear** frequency axis. Both are horizontal and use the same orientation; only the column map changes.

## 2. Target behaviour (what the board does after this change)

| | Behaviour |
| --- | --- |
| Power-up | **Boot check:** a staircase for 1.5 s. It rises from bottom-left to top-right, so you can see the orientation is right. Then live bars. |
| Display | Two modes, both 32 bars over 100 Hz – 8 kHz with the same FFT (1024 points, 39 Hz bins). **LOG** = hybrid-log columns (current FULL mode); **LINEAR** = equal-width columns (current LINEAR mode). No peak dots, no status pixels, no digits. |
| Orientation | Fixed at compile time in `app_config.h`, set once from the T1 probe. **Not** changeable from the buttons or NVS. |
| MODE button | Short press = toggle LOG ↔ LINEAR, saved in NVS. Long press = next brightness (0, 2, 5, 9, 15), saved. |
| LISTEN button | Short press = stop / start listening (as now: display blanks while stopped). Long press = nothing. |
| NVS | Mode (LOG/LINEAR) and brightness. Power-up default: LOG. |
| Serial | Unchanged formats (`FRAME`, `TONE`, `RATE`, `DISPLAY`, `RAW`) so `tools/*.py` keep working. |

## 3. Decisions (copy into the PLAN decision log, date 05/11)

| Decision | Alternatives | Why |
| --- | --- | --- |
| Orientation found by a **raw-register probe** (4 single LEDs), then fixed in `app_config.h` | Keep stepping through 16 orientations by eye | Three single-LED photos fully decide the 4 flags, with no guessing. The result is evidence for the report and can't drift. |
| Orientation **not** stored in NVS; no button for it | LISTEN long press + NVS (30/10) | A wrong saved value kept coming back after reflashing. The mounting never changes, so a compile-time constant is enough. |
| **Two display modes: LOG and LINEAR**, same range (100 Hz – 8 kHz) and FFT | Full / bass / linear (+ tone finder) | Joe's choice, 5 Nov. Bass/voice changed the FFT and the range, so it looked random. With the same range and only the axis changing, a press shows exactly what the log axis does. That is the log-vs-linear decision shown live in the demo. |
| MODE short = toggle the mode, MODE long = brightness | Brightness on the short press | The mode is what the demo uses; brightness is set once. |
| NVS namespace renamed (e.g. `"sv2"`) | Erase flash by hand | Old `mode` = 2 (bass) and `orient` = 9 values on Joe's board can't leak back in. |
| Bass/voice mode and tone-finder display removed from `main/` | Keep behind flags | Dead paths behind flags were part of the confusion. The `tone_finder` component and `TONE` lines stay, because the accuracy tests use them. |

## 4. Tasks

### T1 — Orientation probe in bring-up 01 (do first; Joe runs it)

In `bringup/01_matrix/main/main.c`, **replace step 3 (the 16-way orientation sweep)** with a probe. Use the existing `raw_bit()` helper and the same device index convention as `frame_to_device_rows()`, i.e. `out[dev * 8 + reg]`.

Each step lasts 5 s, adds one LED to what is already lit, and logs one line. Then the whole sequence repeats:

| Step | Lit (cumulative) | Log line |
| --- | --- | --- |
| P1 | dev 0, reg 0, bit 0 — the **origin O** | `PROBE P1 origin: dev0 reg0 bit0` |
| P2 | + dev 0, reg 0, bit 7 | `PROBE P2: + dev0 reg0 bit7 (which way from O?)` |
| P3 | + dev 0, reg 7, bit 0 | `PROBE P3: + dev0 reg7 bit0 (which way from O?)` |
| P4 | + dev 1, reg 0, bit 0 | `PROBE P4: + dev1 reg0 bit0 (which module?)` |

Before the loop, log the viewing rule: `PROBE: hold the strip as it will sit in the demo; 'left/right/up/down' as you look at it`.

Keep steps 1, 2 and 4 (test mode, raw bits, soak). Update the file's header comment and the bring-up 01 section of `bringup/README.md`.

**Turning Joe's answers into flags.** Joe reports four things: P2 relative to O, P3 relative to O, which module O is in, and which module P4 is in. Put this table in `bringup/README.md` and use it:

| Joe sees | Set |
| --- | --- |
| P2 is **left or right** of O (same row) | `TRANSPOSE = false` |
| P2 is **above or below** O (same column) | `TRANSPOSE = true` |
| TRANSPOSE false: P2 **left** of O / **right** of O | `FLIP_X = false` / `true` |
| TRANSPOSE false: P3 **above** O / **below** O | `FLIP_Y = false` / `true` |
| TRANSPOSE true: P2 **above** O / **below** O | `FLIP_Y = false` / `true` |
| TRANSPOSE true: P3 **right** of O / **left** of O | `FLIP_X = false` / `true` |
| O is in the **leftmost** module / the **rightmost** module | `REVERSE_DEVICES = false` / `true` |

**Sanity checks:**
- P2 and P3 must be at right angles to each other, and each must be 7 LEDs from O.
- P4 must be in the module next to O's.

If either check fails, stop and tell Joe: the chain or the driver's device order is not what `frame_to_device_rows()` assumes.

(Derivation, from `frame_to_device_rows()`. Without transpose, `reg = ly'` and `bit = 7 − lx'`, so bit 7 is lx' = 0 (left) and reg 7 is ly' = 7 (top). With transpose, `reg = lx'` and `bit = ly'`, so bit 7 is ly' = 7 (top) and reg 7 is lx' = 7 (right). Here lx' and ly' are the frame coordinates after the flips.)

**Host test.** Add a test to `host_tests/test_frame_gfx.c`. For each of the 16 flag combinations, render the frame pixel the table says O should be, and check that it lands on dev 0, reg 0, bit 0 (or on the right device when reversed). This shows the table and the mapping code agree.

### T2 — Fixed orientation (after Joe's probe answers)

- Set `APP_ORIENT_REVERSE_DEVICES / FLIP_X / FLIP_Y / TRANSPOSE` from T1. Comment each one with the evidence: `/* T1 probe 2026-11-05: P2 left of O ... */`.
- Delete `APP_ORIENT_DEFAULT_K`, `APP_STAIRCASE_ORIENT_MS`, `display_task_set_orientation()`, `s_req_orient`, `orient_from_k()` and the "orientation changed → staircase" path.
- `display_task` builds its `frame_orient_t` once from the four `APP_ORIENT_*` flags.
- `APP_STAIRCASE_BOOT_MS 1500`: show the staircase once at power-up (this is the boot check), and log `ORIENT fixed: R=.. FX=.. FY=.. T=..`.

### T3 — Two display modes: LOG and LINEAR

- Exactly two modes. Reduce `app_mode_t` to `APP_MODE_LOG = 0` and `APP_MODE_LINEAR = 3`. Using the old enum numbers keeps the `mode` field in the `FRAME` line meaning the same as in older logs, so `tools/logparse.py` and `frames.py` keep working; update the name table in `frames.py`. Change `APP_MODE_COUNT` and the "next mode" code to match.
- Both modes: FFT 1024, no decimation, range `APP_FULL_F_MIN_HZ`–`APP_FULL_F_MAX_HZ` (100 Hz – 8 kHz). The only difference is `BAND_MAP_HYBRID_LOG` versus `BAND_MAP_LINEAR` in `band_map_build()`. Make the linear range use the same constants, so the two modes can't drift apart.
- Keep `audio_task_set_mode()` and the existing re-configure-on-change path. It only rebuilds the column map now, and still logs the column edges, which the R2 accuracy test needs.
- `display_task` already clears the bars when the mode changes; keep that. Draw no mode indicator on the LEDs; the serial log line `mode -> LOG` / `mode -> LINEAR` is enough.
- Remove the bass/voice and tone-finder modes from `main/`. Leave the bass constants (`APP_FFT_N_BASS`, `APP_DECIMATE_BASS`, `APP_BASS_*`) and the decimation code in `spectrum` in place, but unused, with a comment "not used since 05/11". If any header signature changes, update its doc comment and say so in the commit.

### T4 — Buttons

- In `input_task`:
  - MODE short press = toggle LOG ↔ LINEAR (`audio_task_set_mode`), then save;
  - MODE long press = next brightness from `APP_BRIGHTNESS_STEPS`, then save;
  - LISTEN short press = stop/start (as now);
  - LISTEN long press does nothing.
- Log every action at INFO level so a log shows what was pressed.

### T5 — Settings / NVS

- `settings_t` holds `mode` (LOG/LINEAR) and `brightness`; remove `orient`. Rename the NVS namespace so old keys are ignored. Any saved value that isn't LOG or LINEAR loads as LOG.
- Update `settings.h` doc comments, and `main.c`, which no longer passes an orientation.

### T6 — Remove the dead display paths

- In `display_task`, delete the tone-finder digits, status pixels and peak-dot drawing, and the `APP_SHOW_*` flags.
- Keep the `frame_gfx` functions and their host tests, because they are pure, tested code that may come back. Only `main/` stops calling them.
- Bars only: `bar_model_update()` → `frame_draw_bar()` × 32 → `frame_to_device_rows()` → `max7219_write_all()`.

### T7 — Docs, diagrams, evidence trail

Update all of these:
- `docs/LAB_TESTS.md`: Session B buttons paragraph, the checklist lines about modes, orientation and status pixels, and the "values still to measure" table (`APP_ORIENT_*` is now set by A1 / T1).
- `README.md`: the controls section, if it has one.
- `CLAUDE.md` hardware note: "Display orientation is fixed in `APP_ORIENT_*`, found with the bring-up 01 probe."
- `docs/CONTEXT.md` log.
- The decision-log rows from §3 in `docs/PLAN.md`.
- Diagrams: in `docs/diagrams/gen_diagrams.py`, update:
  - the input lane in `fw_flow()`: three actions (MODE short → log/linear, MODE long → brightness, LISTEN short → stop/start), and the dashed request labels become "mode, listening" and "brightness";
  - the display lane text "apply new brightness / rotation" → "apply new brightness";
  - the `fw_low()` "orientation" and "Modes" lines;
  - the button descriptions in `circuit()`.

  Then regenerate and render: run `python3 gen_diagrams.py`, render the SVGs to PNG at device scale factor 2 with Playwright, and move the SVGs and PNGs into `docs/diagrams/` (same names as now).

### T8 — Build and test before handing back

```bash
. $IDF_PATH/export.sh
idf.py build                                   # main firmware, no warnings
(cd bringup/01_matrix && idf.py build)
(cd host_tests && make)                        # all pass, incl. the new orientation test
grep -rn "set_orientation\|APP_SHOW_\|TONE_FINDER\|BASS_VOICE\|APP_MODE_FULL" main/   # should print nothing
```

Commit in steps, each message saying what changed and why: (1) probe; (2) two modes + buttons + NVS; (3) fixed orientation once Joe answers; (4) docs and diagrams.

## 5. What Joe does on the hardware

1. **Probe (after T1):**
   ```bash
   cd bringup/01_matrix && idf.py set-target esp32s3   # first time only
   idf.py build flash -p /dev/ttyACM0 monitor | tee ../../docs/evidence/logs/2026-11-05_A1_probe.txt
   ```
   - Hold the strip exactly as it will sit in the demo.
   - At P1–P4, note where each new LED is: P2 and P3 left/right/up/down of O, and which module (1–4 from the left) O and P4 are in. Photograph P3 (O, P2 and P3 all lit) and P4. Save the photos as `docs/evidence/photos/2026-11-05_A1_probe_P3.jpg` and `..._P4.jpg`.
   - Tell Claude Code the four answers; it does T2.
2. **Main firmware (after T2–T6):** `idf.py build flash -p /dev/ttyACM0 monitor`.
   - Check: the boot staircase rises bottom-left → top-right; then talking or whistling moves the bars.
   - Check: a low hum lights the left bars and a whistle lights the right bars; a MODE short press switches LOG ↔ LINEAR; a long press changes brightness; LISTEN blanks and restores.
   - Take a short video: `docs/evidence/videos/2026-11-05_B_bars.mp4`.
3. **Re-set the noise floor.** The new preamp has much more gain, and the 5 Nov photos show many LEDs lit.
   - Record a 30 s quiet-room log with the display running: `docs/evidence/logs/2026-11-05_B1_quiet_lm358.txt`.
   - Run `python3 tools/frames.py <log>` and set `APP_FLOOR_DB` from its suggestion. Note the 700 Hz interference warning if it appears.
4. **Log vs linear evidence:**
   - Play the same function-generator sweep (100 Hz → 8 kHz) or music clip in each mode and record a log of each: `2026-11-05_R_log.txt` and `2026-11-05_R_linear.txt`.
   - Take a video while pressing MODE mid-sound. In LINEAR mode speech should crowd into the left few columns; in LOG mode it should spread across the strip.

## 6. Done when

- [ ] Every power-up shows the same picture: staircase from bottom-left to top-right, then 32 bars with lows on the left. This holds after reflashing too, with no button presses.
- [ ] Only two modes exist, both horizontal. A MODE short press toggles LOG ↔ LINEAR (remembered after power-off), a long press changes brightness, and LISTEN stops/starts. No button can change the orientation.
- [ ] Builds clean; host tests pass, including the new orientation test; the `grep` in T8 finds nothing.
- [ ] `APP_ORIENT_*` and `APP_FLOOR_DB` each have a comment naming the evidence file that set them.
- [ ] PLAN decision log, CONTEXT, LAB_TESTS, README, CLAUDE.md and the diagrams match the new behaviour.

## 7. Not in scope

- New visual features: peak dots, status pixels, tone digits, animations.
- Changes to the preamp, wiring, sample rate or FFT size.
- Software auto-gain (see CLAUDE.md: bar height is true loudness).
