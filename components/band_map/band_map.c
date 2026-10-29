/**
 * @file band_map.c
 * @brief FFT bins -> display columns — implementation (pure C).
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 * Credits / sources used: none adapted; method described in docs/PLAN.md.
 *
 * Bin k is centred on k * bin_hz and covers (k - 0.5 .. k + 0.5) * bin_hz.
 * Bin 0 (DC) is never used: the mic bias lives there.
 */
#include <math.h>
#include "band_map.h"

static float bin_lo_hz(int k, float bin_hz) { return ((float)k - 0.5f) * bin_hz; }
static float bin_hi_hz(int k, float bin_hz) { return ((float)k + 0.5f) * bin_hz; }

/* Equal number of bins per column (what every previous prototype did). */
static void build_linear(band_map_t *map, int b0, int b1, int cols)
{
    int total = b1 - b0 + 1;
    for (int c = 0; c < cols; c++) {
        map->first_bin[c] = b0 + (c * total) / cols;
        map->last_bin[c] = b0 + ((c + 1) * total) / cols - 1;
    }
}

/*
 * Log spacing, but never narrower than one bin. Column by column from the
 * bottom: split what is left of the range (lo .. top) into equal ratios for the
 * columns still to fill, take the first share, and round to whole bins.
 * Where one log share is thinner than a bin, the column gets exactly one bin;
 * the remaining range is then re-split, so log spacing takes over higher up
 * without leaving the top columns short.
 */
static void build_hybrid_log(band_map_t *map, int b0, int b1, int cols, float bin_hz)
{
    float top = bin_hi_hz(b1, bin_hz);
    int b = b0;
    for (int c = 0; c < cols; c++) {
        int remaining = cols - c;
        int last;
        if (remaining == 1) {
            last = b1;
        } else {
            float lo = bin_lo_hz(b, bin_hz);
            float hi = lo * powf(top / lo, 1.0f / (float)remaining);
            last = (int)lroundf(hi / bin_hz - 0.5f);   /* bin whose upper edge is nearest hi */
            if (last < b) last = b;                                  /* at least one bin */
            if (last > b1 - (remaining - 1)) last = b1 - (remaining - 1);   /* one each left */
        }
        map->first_bin[c] = b;
        map->last_bin[c] = last;
        b = last + 1;
    }
}

int band_map_build(band_map_t *map, const band_map_cfg_t *cfg)
{
    if (!map || !cfg) return -1;
    if (cfg->cols < 1 || cfg->cols > BAND_MAP_MAX_COLS) return -1;
    if (cfg->bin_hz <= 0.0f || cfg->n_bins < 2) return -1;
    if (cfg->f_min_hz < 0.0f || cfg->f_max_hz <= cfg->f_min_hz) return -1;
    float nyquist = cfg->bin_hz * (float)cfg->n_bins;
    if (cfg->f_max_hz > nyquist) return -1;

    int b0 = (int)lroundf(cfg->f_min_hz / cfg->bin_hz);
    int b1 = (int)lroundf(cfg->f_max_hz / cfg->bin_hz);
    if (b0 < 1) b0 = 1;
    if (b1 > cfg->n_bins - 1) b1 = cfg->n_bins - 1;
    if (b1 - b0 + 1 < cfg->cols) return -1;   /* not enough bins for one per column */

    map->cols = cfg->cols;
    if (cfg->mode == BAND_MAP_LINEAR) build_linear(map, b0, b1, cfg->cols);
    else                              build_hybrid_log(map, b0, b1, cfg->cols, cfg->bin_hz);

    for (int c = 0; c < cfg->cols; c++) {
        map->f_lo_hz[c] = bin_lo_hz(map->first_bin[c], cfg->bin_hz);
        map->f_hi_hz[c] = bin_hi_hz(map->last_bin[c], cfg->bin_hz);
    }
    return 0;
}

void band_map_apply(const band_map_t *map, const float *bin_db, float *col_db)
{
    for (int c = 0; c < map->cols; c++) {
        float m = bin_db[map->first_bin[c]];
        for (int k = map->first_bin[c] + 1; k <= map->last_bin[c]; k++) {
            if (bin_db[k] > m) m = bin_db[k];
        }
        col_db[c] = m;
    }
}

int band_map_column_for_hz(const band_map_t *map, float hz)
{
    for (int c = 0; c < map->cols; c++) {
        if (hz >= map->f_lo_hz[c] && hz < map->f_hi_hz[c]) return c;
    }
    return -1;
}
