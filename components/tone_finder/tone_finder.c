/**
 * @file tone_finder.c
 * @brief Strongest frequency with parabolic interpolation (pure C).
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 * Credits / sources used: quadratic (parabolic) peak interpolation on log
 *   magnitude — standard method, e.g. J. O. Smith, "Spectral Audio Signal
 *   Processing", section "Quadratic Interpolation of Spectral Peaks".
 */
#include "tone_finder.h"

tone_t tone_find(const float *bin_db, int n_bins, float bin_hz, int min_bin, float min_db)
{
    tone_t t = { .valid = false, .bin = -1, .hz = 0.0f, .db = -1000.0f };
    if (min_bin < 0) min_bin = 0;
    if (n_bins <= min_bin) return t;

    int k = min_bin;
    for (int i = min_bin + 1; i < n_bins; i++) {
        if (bin_db[i] > bin_db[k]) k = i;
    }
    t.bin = k;
    t.db = bin_db[k];
    t.hz = (float)k * bin_hz;
    if (t.db < min_db) return t;
    t.valid = true;

    /*
     * Fit a parabola through (k-1, k, k+1); its top is the refined peak.
     * Only when both neighbours are inside the searched range: a loud DC bin
     * just below min_bin would otherwise drag the estimate down.
     */
    if (k > min_bin && k < n_bins - 1) {
        float a = bin_db[k - 1], b = bin_db[k], c = bin_db[k + 1];
        float denom = a - 2.0f * b + c;
        if (denom < 0.0f) {   /* proper maximum (curve bends down) */
            float p = 0.5f * (a - c) / denom;   /* offset in bins */
            if (p > 0.5f) p = 0.5f;             /* k is the max, so |p| <= 0.5 in theory; */
            if (p < -0.5f) p = -0.5f;           /* clamp against rounding */
            t.hz = ((float)k + p) * bin_hz;
            t.db = b - 0.25f * (a - c) * p;
        }
    }
    return t;
}
