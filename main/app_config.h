/**
 * @file app_config.h
 * @brief Every pin, rate and tunable number in one place.
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
#define APP_PIN_MIC              1    /* MAX9814 OUT -> GPIO1 = ADC1 channel 0 */
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
#define APP_BRIGHTNESS_DEFAULT   2                   /* 0..15, low = less power */
/* Orientation of the 4-in-1 module — set from bring-up 01 results */
#define APP_ORIENT_REVERSE_DEVICES  false
#define APP_ORIENT_FLIP_X           false
#define APP_ORIENT_FLIP_Y           false
#define APP_ORIENT_TRANSPOSE        false

/* ---------------- Sampling and FFT ---------------- */
#define APP_SAMPLE_RATE_HZ       40000   /* requested; check S3 limit in soc_caps.h */
#define APP_FFT_N                1024    /* bins = N/2; bin width = rate / N */
#define APP_DECIMATE_FULL        1
#define APP_DECIMATE_BASS        4       /* bass/voice mode: 10 kHz effective */
#define APP_USE_WINDOW           1       /* Hann on (leakage test turns it off) */

/* ---------------- Column mapping ---------------- */
#define APP_FULL_F_MIN_HZ        100.0f
#define APP_FULL_F_MAX_HZ        8000.0f
#define APP_BASS_F_MIN_HZ        50.0f
#define APP_BASS_F_MAX_HZ        2500.0f

/* ---------------- Levels (MEASURE) ---------------- */
#define APP_FLOOR_DB             (-60.0f)   /* MEASURE: quiet-room noise floor */
#define APP_DB_PER_ROW           4.0f       /* 8 rows = 32 dB */
#define APP_FALL_ROWS_PER_S      20.0f
#define APP_PEAK_HOLD_S          0.5f
#define APP_PEAK_FALL_ROWS_PER_S 6.0f

/* ---------------- Status row thresholds (MEASURE) ---------------- */
#define APP_SILENCE_RMS          8.0f       /* MEASURE: raw counts */
#define APP_CLIP_MARGIN          16         /* raw within this of 0 or 4095 = clipping */
#define APP_TONE_MIN_DB          (-50.0f)   /* MEASURE: tone-finder "nothing there" level */

/* ---------------- Tasks ---------------- */
/* Audio (sampling + FFT) on core 0, display + buttons on core 1 */
#define APP_AUDIO_TASK_CORE      0
#define APP_AUDIO_TASK_PRIO      6
#define APP_AUDIO_TASK_STACK     8192
#define APP_DISPLAY_TASK_CORE    1
#define APP_DISPLAY_TASK_PRIO    5
#define APP_DISPLAY_TASK_STACK   4096
#define APP_DISPLAY_PERIOD_MS    25         /* 40 fps redraw */
#define APP_INPUT_TASK_CORE      1
#define APP_INPUT_TASK_PRIO      3
#define APP_INPUT_TASK_STACK     3072
#define APP_INPUT_PERIOD_MS      10

/* ---------------- Debug ---------------- */
#define APP_DEBUG_STREAM_DEFAULT 1          /* print FRAME/TONE lines over serial */
