/**
 * @file app_types.h
 * @brief Types shared between the application tasks.
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "band_map.h"
#include "tone_finder.h"

/*
 * Two display modes (05/11). Same FFT and range (100 Hz - 8 kHz); only the
 * column map differs. The numbers are the old enum values, so the mode field
 * in FRAME lines means the same as in older logs (1 = bass/voice and
 * 2 = tone finder were removed).
 */
typedef enum {
    APP_MODE_LOG    = 0,    /**< hybrid-log columns (was "full") */
    APP_MODE_LINEAR = 3,    /**< equal-width columns, for the log-vs-linear comparison */
} app_mode_t;

#define APP_MODE_COUNT 2    /**< number of modes (not a valid value: values are 0 and 3) */

static inline bool app_mode_valid(int m) { return m == APP_MODE_LOG || m == APP_MODE_LINEAR; }
static inline app_mode_t app_mode_next(app_mode_t m) { return m == APP_MODE_LOG ? APP_MODE_LINEAR : APP_MODE_LOG; }
static inline const char *app_mode_name(app_mode_t m) { return m == APP_MODE_LINEAR ? "LINEAR" : "LOG"; }

/**
 * One analysed frame, sent from audio_task to display_task.
 * The queue holds only the latest frame (xQueueOverwrite): if the display
 * falls behind it skips old frames instead of lagging (latency, R3).
 */
typedef struct {
    uint32_t   seq;                        /**< frame counter */
    int64_t    t_us;                       /**< esp_timer time when capture finished */
    app_mode_t mode;
    int        cols;
    float      col_db[BAND_MAP_MAX_COLS];  /**< level per display column */
    tone_t     tone;                       /**< strongest tone (all modes) */
    int        tone_col;                   /**< column the tone falls in, -1 if outside the map */
    uint32_t   status;                     /**< frame_status_t bits */
    uint32_t   process_us;                 /**< time spent in FFT + mapping */
} audio_frame_t;
