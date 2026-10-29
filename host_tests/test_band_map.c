/**
 * @file test_band_map.c
 * Laptop tests for band_map: linear (baseline) and hybrid log mapping.
 * Prints the hybrid column table — copy it into the Design write-up.
 */
#include <stdio.h>
#include "band_map.h"
#include "test_util.h"

static void check_contiguous(const band_map_t *m, int n_bins)
{
    for (int c = 0; c < m->cols; c++) {
        CHECK(m->first_bin[c] >= 1);
        CHECK(m->first_bin[c] <= m->last_bin[c]);
        CHECK(m->last_bin[c] < n_bins);
        if (c > 0) CHECK(m->first_bin[c] == m->last_bin[c - 1] + 1);   /* no gaps, no overlap */
    }
}

int main(void)
{
    band_map_t m;

    /* Aidan's setup: 96 kHz / 512 = 187.5 Hz bins, linear 0-6 kHz -> one bin per column */
    band_map_cfg_t aidan = {BAND_MAP_LINEAR, 32, 0.0f, 6000.0f, 187.5f, 256};
    CHECK(band_map_build(&m, &aidan) == 0);
    check_contiguous(&m, 256);
    for (int c = 0; c < 32; c++) CHECK(m.first_bin[c] == c + 1 && m.last_bin[c] == c + 1);

    /* Ours: 40 kHz / 1024 = 39.0625 Hz bins, 100 Hz - 8 kHz */
    const float bin = 40000.0f / 1024.0f;
    band_map_cfg_t lin = {BAND_MAP_LINEAR, 32, 100.0f, 8000.0f, bin, 512};
    CHECK(band_map_build(&m, &lin) == 0);
    check_contiguous(&m, 512);

    band_map_cfg_t hyb = {BAND_MAP_HYBRID_LOG, 32, 100.0f, 8000.0f, bin, 512};
    CHECK(band_map_build(&m, &hyb) == 0);
    check_contiguous(&m, 512);
    CHECK(m.last_bin[0] == m.first_bin[0]);        /* bottom columns: one bin each */
    CHECK(m.last_bin[1] == m.first_bin[1]);
    CHECK_NEAR(m.f_hi_hz[31], 8000.0, bin);        /* top edge reaches 8 kHz */
    CHECK_NEAR(m.f_lo_hz[0], 100.0, bin);
    for (int c = 1; c < 32; c++) {                 /* widths never shrink going up */
        int w = m.last_bin[c] - m.first_bin[c], wp = m.last_bin[c - 1] - m.first_bin[c - 1];
        CHECK(w >= wp);
    }
    printf("  hybrid 100-8000 Hz, %.2f Hz bins:\n  col  bins      Hz\n", bin);
    for (int c = 0; c < 32; c++)
        printf("  %2d  %3d-%3d  %6.0f-%6.0f\n", c, m.first_bin[c], m.last_bin[c], m.f_lo_hz[c], m.f_hi_hz[c]);

    /* bass/voice mode: 10 kHz / 512 = 19.53 Hz bins, 50-2500 Hz */
    band_map_cfg_t bass = {BAND_MAP_HYBRID_LOG, 32, 50.0f, 2500.0f, 10000.0f / 512, 256};
    CHECK(band_map_build(&m, &bass) == 0);
    check_contiguous(&m, 256);

    /* invalid configs */
    band_map_cfg_t bad = hyb;
    bad.f_max_hz = 30000.0f;                       /* above Nyquist (20 kHz) */
    CHECK(band_map_build(&m, &bad) == -1);
    bad = hyb; bad.cols = 0;
    CHECK(band_map_build(&m, &bad) == -1);
    bad = hyb; bad.cols = 33;
    CHECK(band_map_build(&m, &bad) == -1);
    bad = hyb; bad.f_min_hz = 100.0f; bad.f_max_hz = 500.0f;   /* ~10 bins for 32 columns */
    CHECK(band_map_build(&m, &bad) == -1);

    /* apply: one loud bin lands in its column, column = max of its bins */
    CHECK(band_map_build(&m, &hyb) == 0);
    float bins[512], cols[32];
    for (int k = 0; k < 512; k++) bins[k] = -90.0f;
    int k1k = 1000.0f / bin + 0.5f;
    bins[k1k] = -10.0f;
    band_map_apply(&m, bins, cols);
    int c1k = band_map_column_for_hz(&m, 1000.0f);
    CHECK(c1k >= 0);
    CHECK_NEAR(cols[c1k], -10.0, 1e-6);
    for (int c = 0; c < 32; c++) if (c != c1k) CHECK_NEAR(cols[c], -90.0, 1e-6);

    /* column_for_hz */
    CHECK(band_map_column_for_hz(&m, 440.0f) >= 0);
    CHECK(band_map_column_for_hz(&m, 440.0f) < c1k);
    CHECK(band_map_column_for_hz(&m, 20.0f) == -1);
    CHECK(band_map_column_for_hz(&m, 12000.0f) == -1);

    return TEST_RESULT();
}
