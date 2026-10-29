/**
 * @file band_map.h
 * @brief Which FFT bins feed which display column. Pure C — no ESP-IDF.
 *
 * Two modes:
 *  - LINEAR: equal-width columns from f_min to f_max (what every previous
 *    prototype did — kept as the baseline for the before/after comparison).
 *  - HYBRID_LOG: log-spaced columns, except that a column is never narrower
 *    than one bin. At the bottom (where log bands would be thinner than a bin)
 *    each column takes one bin; log spacing takes over above that.
 *    See docs/PLAN.md, "Numbers for the write-up".
 *
 * A column's value is the loudest bin inside it (max, not average), so a
 * pure tone shows at full height wherever it lands.
 */
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#define BAND_MAP_MAX_COLS 32

typedef enum {
    BAND_MAP_LINEAR = 0,
    BAND_MAP_HYBRID_LOG,
} band_map_mode_t;

typedef struct {
    band_map_mode_t mode;
    int   cols;        /**< columns to fill, <= BAND_MAP_MAX_COLS */
    float f_min_hz;    /**< lower edge of column 0 */
    float f_max_hz;    /**< upper edge of the last column (<= Nyquist) */
    float bin_hz;      /**< FFT bin width (spectrum_bin_hz()) */
    int   n_bins;      /**< number of FFT bins available (spectrum_n_bins()) */
} band_map_cfg_t;

typedef struct {
    int   cols;
    int   first_bin[BAND_MAP_MAX_COLS];   /**< inclusive */
    int   last_bin[BAND_MAP_MAX_COLS];    /**< inclusive, >= first_bin */
    float f_lo_hz[BAND_MAP_MAX_COLS];     /**< column edges, for logs and tests */
    float f_hi_hz[BAND_MAP_MAX_COLS];
} band_map_t;

/**
 * Work out the bin ranges for every column.
 * @return 0 on success, -1 if cfg is invalid (e.g. f_max above Nyquist,
 *         cols out of range, or not enough bins for the columns asked for).
 */
int band_map_build(band_map_t *map, const band_map_cfg_t *cfg);

/** col_db[c] = max of bin_db[first_bin[c] .. last_bin[c]] for every column. */
void band_map_apply(const band_map_t *map, const float *bin_db, float *col_db);

/** Column a frequency falls in, or -1 if outside the map. Used by accuracy tests. */
int band_map_column_for_hz(const band_map_t *map, float hz);

#ifdef __cplusplus
}
#endif
