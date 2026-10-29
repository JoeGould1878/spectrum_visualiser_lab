/**
 * @file spectrum.h
 * @brief Raw ADC frame -> magnitude spectrum in dB.
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
 *
 * Steps, in order (each one is a design decision with its own evidence):
 *   1. Frame stats on the raw samples (min/max for clipping, RMS for silence).
 *   2. Convert to float and remove the DC offset (MAX9814 bias ~1.25 V).
 *   3. Optional decimation: low-pass filter, then keep every Nth sample
 *      (bass/voice mode — finer bins; the filter stops aliasing).
 *   4. Optional Hann window (leakage test: window on vs off).
 *   5. Real FFT (esp-dsp), magnitude, dB.
 *
 * Output has n/2 bins; bin k is centred on k * spectrum_bin_hz().
 * Uses esp-dsp (Espressif) — credit it in spectrum.c and the README.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    size_t   fft_n;            /**< FFT size after decimation, power of 2 (e.g. 1024) */
    uint32_t sample_rate_hz;   /**< ADC rate before decimation (measured value!) */
    int      decimate;         /**< 1 = full mode, 4 = bass/voice mode */
    bool     use_window;       /**< Hann window on/off */
} spectrum_cfg_t;

typedef struct {
    uint16_t raw_min;          /**< lowest raw sample in the frame */
    uint16_t raw_max;          /**< highest raw sample (near 0 or 4095 = clipping) */
    float    rms;              /**< RMS after DC removal, in raw counts */
} spectrum_stats_t;

/** Allocate buffers and set up the FFT tables. Call again to change config. */
esp_err_t spectrum_init(const spectrum_cfg_t *cfg);

/** Raw samples needed per call: fft_n * decimate. */
size_t spectrum_input_len(void);

/** Number of output bins: fft_n / 2. */
size_t spectrum_n_bins(void);

/** Width of one bin in Hz: (sample_rate_hz / decimate) / fft_n. */
float spectrum_bin_hz(void);

/**
 * Process one frame.
 * @param raw       spectrum_input_len() raw ADC samples
 * @param mag_db    out: spectrum_n_bins() values, dB (reference documented in .c)
 * @param stats     out: frame statistics (may be NULL)
 */
esp_err_t spectrum_compute(const uint16_t *raw, float *mag_db, spectrum_stats_t *stats);

/** Free buffers. */
void spectrum_deinit(void);

#ifdef __cplusplus
}
#endif
