# Spec: simplify the display (one mode, fixed orientation)

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

**Goal:** one picture, always the same, after every power-up. The strip is horizontal and has 32 bars. Low notes are on the left. Bars rise from the bottom edge.

## 2. Target behaviour (what the board does after this change)

| | Behaviour |
| --- | --- |
| Power-up | **Boot check:** a staircase for 1.5 s. It rises from bottom-left to top-right, so you can see the orientation is right. Then live bars. |
| Display | One mode: 32 bars, hybrid-log columns 100 Hz – 8 kHz (current FULL mode). No peak dots, no status pixels, no digits. |
| Orientation | Fixed at compile time in `app_config.h`, set once from the T1 probe. **Not** changeable from the buttons or NVS. |
| MODE button | Short press = next brightness (0, 2, 5, 9, 15), saved in NVS. Long press = nothing. |
| LISTEN button | Short press = stop / start listening (as now: display blanks while stopped). Long press = nothing. |
| NVS | Brightness only. |
| Serial | Unchanged formats (`FRAME`, `TONE`, `RATE`, `DISPLAY`, `RAW`) so `tools/*.py` keep working. |

## 3. Decisions (copy into the PLAN decision log, date 05/11)

| Decision | Alternatives | Why |
| --- | --- | --- |
| Orientation found by a **raw-register probe** (4 single LEDs), then fixed in `app_config.h` | Keep stepping through 16 orientations by eye | Three single-LED photos fully decide the 4 flags, with no guessing. The result is evidence for the report and can't drift. |
| Orientation **not** stored in NVS; no button for it | LISTEN long press + NVS (30/10) | A wrong saved value kept coming back after reflashing. The mounting never changes, so a compile-time constant is enough. |
| **One display mode** (hybrid log 100 Hz – 8 kHz) | MODE cycles full / bass / linear | Viewers read the other modes as random. One mode is easier to explain in the demo. |
| Linear mapping kept as a **compile-time** switch `APP_BAND_MAPPING` | Runtime mode | Still needed for the log-vs-linear evidence test (the "significant decision" in PLAN). Flash twice, record both. |
| MODE short press = brightness | Brightness on a long press | It's the only setting left, so it gets the easy press. |
| NVS namespace renamed (e.g. `"sv2"`) | Erase flash by hand | Old `mode` = 2 and `orient` = 9 values on Joe's board can't leak back in. |
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

### T3 — One display mode

- Add `APP_BAND_MAPPING` to `app_config.h` with value `BAND_MAP_HYBRID_LOG` (or `BAND_MAP_LINEAR` for the evidence test only). Comment it: "flash with LINEAR for the log-vs-linear test, then set it back".
- In `audio_task`, configure once at start: FFT 1024, no decimation, `APP_FULL_F_MIN_HZ`–`APP_FULL_F_MAX_HZ`, `APP_BAND_MAPPING`. Remove the runtime mode switch, `audio_task_set_mode()` and the bass/voice setup.
- Keep the `mode` field in the `FRAME` line so `tools/logparse.py` still parses it. Send `0` for hybrid log and `3` for linear (the old enum numbers), so old logs and new logs mean the same thing in `frames.py`.
- You can shrink `app_mode_t` or replace it with the band-mapping value. Choose whichever keeps the change smallest, and update the headers' doc comments if a signature changes (and say so in the commit).
- Leave the bass/voice constants (`APP_FFT_N_BASS`, `APP_DECIMATE_BASS`, `APP_BASS_*`) and the decimation code in `spectrum` in place, but unused. Mark them in a comment as "not used since 05/11".

### T4 — Buttons

- In `input_task`:
  - MODE short press = next brightness from `APP_BRIGHTNESS_STEPS`, then save;
  - LISTEN short press = stop/start (as now);
  - both long presses do nothing.
- Log every action at INFO level so a log shows what was pressed.

### T5 — Settings / NVS

- `settings_t` holds `brightness` only. Rename the NVS namespace so old keys are ignored.
- Update `settings.h` doc comments, and `main.c`, which no longer passes a mode or orientation.

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
  - the input lane in `fw_flow()`: two actions (MODE → brightness, LISTEN → stop/start), and the dashed request labels become "listening" and "brightness";
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
grep -rn "set_orientation\|APP_SHOW_\|TONE_FINDER\|BASS_VOICE" main/   # should print nothing
```

Commit in steps, each message saying what changed and why: (1) probe; (2) one mode + buttons + NVS; (3) fixed orientation once Joe answers; (4) docs and diagrams.

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
   - Check: a low hum lights the left bars and a whistle lights the right bars; MODE changes brightness; LISTEN blanks and restores.
   - Take a short video: `docs/evidence/videos/2026-11-05_B_bars.mp4`.
3. **Re-set the noise floor.** The new preamp has much more gain, and the 5 Nov photos show many LEDs lit.
   - Record a 30 s quiet-room log with the display running: `docs/evidence/logs/2026-11-05_B1_quiet_lm358.txt`.
   - Run `python3 tools/frames.py <log>` and set `APP_FLOOR_DB` from its suggestion. Note the 700 Hz interference warning if it appears.
4. **Log vs linear evidence:**
   - Flash once with `APP_BAND_MAPPING BAND_MAP_LINEAR`. Record the same sweep or music clip as with hybrid log, and take a photo or video of each.
   - Set it back to hybrid log afterwards.

## 6. Done when

- [ ] Every power-up shows the same picture: staircase from bottom-left to top-right, then 32 bars with lows on the left. This holds after reflashing too, with no button presses.
- [ ] No button can change the orientation or the mode. MODE changes brightness; LISTEN stops/starts.
- [ ] Builds clean; host tests pass, including the new orientation test; the `grep` in T8 finds nothing.
- [ ] `APP_ORIENT_*` and `APP_FLOOR_DB` each have a comment naming the evidence file that set them.
- [ ] PLAN decision log, CONTEXT, LAB_TESTS, README, CLAUDE.md and the diagrams match the new behaviour.

## 7. Not in scope

- New visual features: peak dots, status pixels, tone digits, animations.
- Changes to the preamp, wiring, sample rate or FFT size.
- Software auto-gain (see CLAUDE.md: bar height is true loudness).
