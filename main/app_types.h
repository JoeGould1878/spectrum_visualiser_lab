/**
 * @file app_types.h
 * @brief Types shared between the application tasks.
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
 */
#pragma once

#include <stdint.h>
#include "band_map.h"
#include "tone_finder.h"

typedef enum {
    APP_MODE_FULL = 0,      /**< 100 Hz - 8 kHz, hybrid log columns */
    APP_MODE_BASS_VOICE,    /**< decimated: finer bins, 50 Hz - 2.5 kHz */
    APP_MODE_TONE_FINDER,   /**< strongest frequency shown as digits */
    APP_MODE_LINEAR,        /**< baseline: Aidan-style linear columns, for comparison */
    APP_MODE_COUNT
} app_mode_t;

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
