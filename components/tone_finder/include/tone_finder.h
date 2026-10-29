/**
 * @file tone_finder.h
 * @brief Strongest frequency in a spectrum, in Hz (flagship "tone-finder"
 *        mode). Pure C — no ESP-IDF.
 *
 * Finds the loudest bin, then refines its position using the two neighbouring
 * bins (fitting a parabola through the three dB values), so the answer can
 * fall between bins. Accuracy is tested against known tones
 * (test "Tone-finder accuracy" in docs/PLAN.md).
 */
#pragma once

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    bool  valid;     /**< false if nothing above min_db (silence) */
    int   bin;       /**< loudest bin index */
    float hz;        /**< refined frequency estimate */
    float db;        /**< level of the peak */
} tone_t;

/**
 * @param bin_db    spectrum in dB, n_bins values
 * @param bin_hz    width of one bin
 * @param min_bin   ignore bins below this (skip DC / rumble)
 * @param min_db    report invalid if the peak is quieter than this
 */
tone_t tone_find(const float *bin_db, int n_bins, float bin_hz, int min_bin, float min_db);

#ifdef __cplusplus
}
#endif
