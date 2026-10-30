/**
 * @file bar_model.h
 * @brief Column level in dB -> bar height (0..8) with smoothing and peak dots.
 *        Pure C — no ESP-IDF.
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
 *
 *  - Scaling: rows = (col_db - floor_db) / db_per_row, clamped to 0..rows.
 *    floor_db is the noise floor MEASURED in a quiet room (requirement R5).
 *  - Smoothing: bars jump up immediately (fast rise) and fall at
 *    fall_rows_per_s (slow fall), so they don't flicker.
 *  - Peak dots: the highest recent level is held for peak_hold_s, then falls.
 *
 * Deliberately no automatic gain: bar height should show real loudness so the
 * display is honest about level (decision log, 29/10 and 30/10).
 */
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#define BAR_MODEL_MAX_COLS 32

typedef struct {
    int   rows;               /**< display height, 8 */
    float floor_db;           /**< level that maps to 0 rows */
    float db_per_row;         /**< e.g. 4 dB/row -> 8 rows = 32 dB */
    float fall_rows_per_s;    /**< bar fall speed */
    float peak_hold_s;        /**< how long a peak dot stays put */
    float peak_fall_rows_per_s;
} bar_model_cfg_t;

typedef struct {
    bar_model_cfg_t cfg;
    int   cols;
    float level[BAR_MODEL_MAX_COLS];     /**< smoothed height, in rows (fractional) */
    float peak[BAR_MODEL_MAX_COLS];      /**< peak-dot height, in rows */
    float peak_age_s[BAR_MODEL_MAX_COLS];
} bar_model_t;

/** Reset every column to 0. */
void bar_model_init(bar_model_t *m, const bar_model_cfg_t *cfg, int cols);

/** Feed one frame of column levels (dB). dt_s = time since the last update. */
void bar_model_update(bar_model_t *m, const float *col_db, float dt_s);

/** Bar height to draw for a column, 0..rows. */
int bar_model_height(const bar_model_t *m, int col);

/** Row of the peak dot for a column (1..rows), or 0 for no dot. */
int bar_model_peak_row(const bar_model_t *m, int col);

#ifdef __cplusplus
}
#endif
