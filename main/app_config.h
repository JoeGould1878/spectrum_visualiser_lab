/**
 * @file app_config.h
 * @brief Every pin, rate and tunable number in one place.
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
 *
 * Board: Freenove ESP32-S3-WROOM (camera ribbon UNPLUGGED — the camera uses
 * GPIO 4-13 and 15-18). Avoid: GPIO 2 (on-board LED), 0/3/45/46 (strapping),
 * 19/20 (USB), 35-37 (PSRAM).
 *
 * Values marked MEASURE are placeholders until a test gives the real number;
 * when you change one, add a line to the decision log in docs/PLAN.md.
 */
#pragma once

/* ---------------- Pins (confirm at bring-up) ---------------- */
#define APP_PIN_MIC              1    /* LM358 preamp output (via 4.7k/2.2n filter) -> GPIO1 = ADC1 channel 0 */
#define APP_PIN_MAX7219_DIN      11
#define APP_PIN_MAX7219_CLK      12
#define APP_PIN_MAX7219_CS       10
#define APP_PIN_BTN_MODE         14   /* to GND, internal pull-up */
#define APP_PIN_BTN_LISTEN       21   /* to GND, internal pull-up */

/* ---------------- Display ---------------- */
#define APP_MAX7219_HOST         SPI2_HOST
#define APP_MAX7219_DEVICES      4
#define APP_MAX7219_CLOCK_HZ     (1 * 1000 * 1000)   /* start slow, raise once stable */
#define APP_DISPLAY_COLS         32
#define APP_DISPLAY_ROWS         8
#define APP_BRIGHTNESS_DEFAULT   0                   /* 0..15. 0 since 05/11: display interference is ~27 dB lower than at 15
                                                        (2026-11-05_B1_covered_b15/b0.txt); APP_FLOOR_DB is measured at 0 */
/* Orientation of the 4-in-1 module: fixed at compile time (05/11), not
 * changeable from the buttons or NVS. Set from the bring-up 01 probe,
 * evidence docs/evidence/logs/2026-11-05_A1_probe.txt and
 * docs/evidence/photos/2026-11-05_A1_Probe_P3/P4.jpeg, strip horizontal with
 * the wire end on the right (table in bringup/README.md): */
#define APP_ORIENT_REVERSE_DEVICES  true    /* T1 probe 2026-11-05: O in the rightmost module, P4 in the next one left */
#define APP_ORIENT_FLIP_X           false   /* T1 probe 2026-11-05: P2 left of O */
#define APP_ORIENT_FLIP_Y           true    /* T1 probe 2026-11-05: P3 below O */
#define APP_ORIENT_TRANSPOSE        false   /* T1 probe 2026-11-05: P2 in the same row as O */
#define APP_STAIRCASE_BOOT_MS    1500   /* boot check: staircase rising bottom-left -> top-right, then live bars */

/* ---------------- Sampling and FFT ---------------- */
#define APP_SAMPLE_RATE_HZ       40000   /* requested; S3 allows 611..83333 (SOC_ADC_SAMPLE_FREQ_THRES_*) */
#define APP_SAMPLE_RATE_ACTUAL_HZ 40314  /* measured: median of 172 RATE lines, 2026-11-05 logs (34246..40321; low values = boot) — used for all Hz maths */
#define APP_FFT_N                1024    /* both modes: bins = N/2; bin width = rate / N */
#define APP_DECIMATE_FULL        1
/* Bass/voice mode constants: not used since 05/11 (two modes only, same FFT). */
#define APP_FFT_N_BASS           512     /* not used since 05/11 */
#define APP_DECIMATE_BASS        4       /* not used since 05/11 */
#define APP_USE_WINDOW           1       /* Hann on (leakage test: set 0, reflash, compare) */

/* ---------------- Column mapping ---------------- */
/* LOG and LINEAR both use this range and the same FFT, so a MODE press
 * changes only the column map (one variable at a time). */
#define APP_FULL_F_MIN_HZ        100.0f
#define APP_FULL_F_MAX_HZ        8000.0f
#define APP_BASS_F_MIN_HZ        50.0f     /* not used since 05/11 */
#define APP_BASS_F_MAX_HZ        2500.0f   /* not used since 05/11 */

/* ---------------- Levels (MEASURE) ---------------- */
#define APP_FLOOR_DB             (-40.0f)   /* 2026-11-05_B1_covered_b0: LM358, mic covered, brightness 0, LOG:
                                               typical column p95 -42.6 dB, +3 dB. Interference columns 11-12 and
                                               28-29 (p95 -33..-36 dB) excluded: known limitation, they show
                                               ~2 rows in silence. (Was -46 from a 30/10 log: NPN preamp, bass mode) */
#define APP_DB_PER_ROW           3.0f       /* 8 rows = 24 dB: electret preamp is quiet, speech needs the range */
#define APP_FALL_ROWS_PER_S      20.0f
#define APP_PEAK_HOLD_S          0.5f
#define APP_PEAK_FALL_ROWS_PER_S 6.0f

/* ---------------- Status row thresholds (MEASURE) ---------------- */
#define APP_SILENCE_RMS          8.0f       /* MEASURE: raw counts */
#define APP_CLIP_MARGIN          16         /* raw within this of 0 or 4095 = clipping */
#define APP_TONE_MIN_DB          (-30.0f)   /* floor + 10 dB: below this the tone finder reports no tone */
#define APP_TONE_F_MIN_HZ        50.0f      /* tone-finder ignores bins below this (DC, rumble) */
/* "Above range" pixel: strongest peak above the displayed range is louder than
 * APP_TONE_MIN_DB and within this many dB of the strongest in-range column. */
#define APP_ABOVE_RANGE_MARGIN_DB 6.0f

/* ---------------- Tasks ---------------- */
/* Audio (sampling + FFT) on core 0, display + buttons on core 1 */
#define APP_AUDIO_TASK_CORE      0
#define APP_AUDIO_TASK_PRIO      6
#define APP_AUDIO_TASK_STACK     8192
#define APP_DISPLAY_TASK_CORE    1
#define APP_DISPLAY_TASK_PRIO    5
#define APP_DISPLAY_TASK_STACK   6144       /* float printf + frame buffers; raised from 4096 at review */
#define APP_DISPLAY_PERIOD_MS    25         /* 40 fps redraw */
#define APP_DISPLAY_STALE_MS     500        /* no new audio frame for this long -> blank, not frozen */
#define APP_DISPLAY_RESYNC_MS    1000       /* re-send MAX7219 control registers (glitch recovery) */
#define APP_INPUT_TASK_CORE      1
#define APP_INPUT_TASK_PRIO      3
#define APP_INPUT_TASK_STACK     4096       /* NVS writes + logging; raised from 3072 at review */
#define APP_INPUT_PERIOD_MS      10

/* ---------------- Buttons / settings ---------------- */
#define APP_BTN_DEBOUNCE_MS      30
#define APP_BTN_LONG_MS          800
#define APP_MODE_DEFAULT         APP_MODE_LOG    /* used until a mode is saved */
/* Long press on MODE steps through these brightness levels */
#define APP_BRIGHTNESS_STEPS     {0, 2, 5, 9, 15}

/* Display: plain spectrum bars only (05/11). No peak dots, status pixels or
 * tone digits on the LEDs; tone and status are still logged over serial. */

/* ---------------- Debug ---------------- */
#define APP_DEBUG_STREAM_DEFAULT 1          /* print FRAME/TONE lines over serial */
#define APP_DEBUG_EVERY_N_FRAMES 1          /* 1 = every frame (~39/s); raise if the serial link can't keep up */
