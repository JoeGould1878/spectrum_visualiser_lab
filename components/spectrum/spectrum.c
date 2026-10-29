/**
 * @file spectrum.c
 * @brief DC removal, decimation, window, FFT — implementation.
 *
 * Author: Joe Gould, with Claude (Anthropic) writing the implementation
 * Credits / sources used: esp-dsp (Espressif, Apache-2.0): dsps_fft2r_init_fc32,
 *   dsps_fft2r_fc32, dsps_bit_rev_fc32 and dsps_wind_hann_f32, used as in the
 *   esp-dsp "fft" example (real signal in the real parts, imaginary parts 0).
 *   Decimation filter: windowed-sinc low-pass (standard FIR design, written here).
 *
 * dB reference ("dBFS"): 0 dB = a sine whose amplitude fills the ADC range
 * (2048 counts peak). The window's gain is corrected for, so a pure tone reads
 * the same dB with the window on or off; noise reads a little differently.
 */
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "spectrum.h"
#include "esp_check.h"
#include "esp_heap_caps.h"
#include "dsps_fft2r.h"
#include "dsps_wind_hann.h"

static const char *TAG = "spectrum";

#define FULL_SCALE_AMPL   2048.0f   /* 12-bit ADC, sine peak around mid-scale */
#define DECIM_TAPS        63        /* odd -> symmetric, integer delay */
#define DB_FLOOR          (-140.0f) /* stand-in for log10(0) */

static spectrum_cfg_t s_cfg;
static bool s_ready;
static float *s_signal;   /* full-rate, DC removed: fft_n * decimate */
static float *s_fft;      /* complex interleaved: 2 * fft_n, 16-byte aligned for the S3 FFT */
static float *s_window;   /* fft_n */
static float s_window_gain;
static float s_fir[DECIM_TAPS];

/*
 * Windowed-sinc low-pass for decimation: cut-off at 80 % of the new Nyquist,
 * Blackman window (stopband ~ -74 dB). Removes everything the decimated rate
 * can't represent BEFORE samples are thrown away — otherwise it would alias
 * (fold back) into the bass columns.
 */
static void design_decim_fir(int decimate)
{
    const float fc = 0.8f * 0.5f / (float)decimate;   /* cycles per input sample */
    const int mid = DECIM_TAPS / 2;
    float sum = 0.0f;
    for (int i = 0; i < DECIM_TAPS; i++) {
        int n = i - mid;
        float sinc = n == 0 ? 2.0f * fc : sinf(2.0f * (float)M_PI * fc * n) / ((float)M_PI * n);
        float w = 0.42f - 0.5f * cosf(2.0f * (float)M_PI * i / (DECIM_TAPS - 1))
                        + 0.08f * cosf(4.0f * (float)M_PI * i / (DECIM_TAPS - 1));
        s_fir[i] = sinc * w;
        sum += s_fir[i];
    }
    for (int i = 0; i < DECIM_TAPS; i++) s_fir[i] /= sum;   /* unity gain at DC */
}

esp_err_t spectrum_init(const spectrum_cfg_t *cfg)
{
    ESP_RETURN_ON_FALSE(cfg, ESP_ERR_INVALID_ARG, TAG, "null cfg");
    ESP_RETURN_ON_FALSE(cfg->fft_n >= 64 && cfg->fft_n <= CONFIG_DSP_MAX_FFT_SIZE &&
                        (cfg->fft_n & (cfg->fft_n - 1)) == 0,
                        ESP_ERR_INVALID_ARG, TAG, "fft_n must be a power of 2, 64..%d", CONFIG_DSP_MAX_FFT_SIZE);
    ESP_RETURN_ON_FALSE(cfg->decimate >= 1 && cfg->decimate <= 16, ESP_ERR_INVALID_ARG, TAG, "decimate 1..16");
    ESP_RETURN_ON_FALSE(cfg->sample_rate_hz > 0, ESP_ERR_INVALID_ARG, TAG, "rate");

    spectrum_deinit();
    s_cfg = *cfg;

    /* Twiddle table sized for the largest FFT once; it works for any smaller N. */
    esp_err_t err = dsps_fft2r_init_fc32(NULL, CONFIG_DSP_MAX_FFT_SIZE);
    ESP_RETURN_ON_ERROR(err, TAG, "fft init");

    size_t in_len = cfg->fft_n * cfg->decimate;
    s_signal = malloc(in_len * sizeof(float));
    s_fft = heap_caps_aligned_alloc(16, 2 * cfg->fft_n * sizeof(float), MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
    s_window = malloc(cfg->fft_n * sizeof(float));
    if (!s_signal || !s_fft || !s_window) {
        spectrum_deinit();
        return ESP_ERR_NO_MEM;
    }

    if (cfg->use_window) {
        dsps_wind_hann_f32(s_window, (int)cfg->fft_n);
    } else {
        for (size_t i = 0; i < cfg->fft_n; i++) s_window[i] = 1.0f;
    }
    float sum = 0.0f;
    for (size_t i = 0; i < cfg->fft_n; i++) sum += s_window[i];
    s_window_gain = sum / (float)cfg->fft_n;   /* 0.5 for Hann, 1.0 for none */

    if (cfg->decimate > 1) design_decim_fir(cfg->decimate);

    s_ready = true;
    ESP_LOGI(TAG, "N=%u, decimate %d, %.2f Hz bins, window %s",
             (unsigned)cfg->fft_n, cfg->decimate, spectrum_bin_hz(), cfg->use_window ? "Hann" : "off");
    return ESP_OK;
}

size_t spectrum_input_len(void) { return s_cfg.fft_n * (size_t)s_cfg.decimate; }
size_t spectrum_n_bins(void)    { return s_cfg.fft_n / 2; }

float spectrum_bin_hz(void)
{
    if (s_cfg.fft_n == 0 || s_cfg.decimate == 0) return 0.0f;
    return ((float)s_cfg.sample_rate_hz / (float)s_cfg.decimate) / (float)s_cfg.fft_n;
}

esp_err_t spectrum_compute(const uint16_t *raw, float *mag_db, spectrum_stats_t *stats)
{
    ESP_RETURN_ON_FALSE(s_ready, ESP_ERR_INVALID_STATE, TAG, "not initialised");
    ESP_RETURN_ON_FALSE(raw && mag_db, ESP_ERR_INVALID_ARG, TAG, "null arg");
    const size_t n = s_cfg.fft_n;
    const size_t in_len = spectrum_input_len();
    const int d = s_cfg.decimate;

    /* 1. Frame stats on raw samples */
    uint16_t lo = 0xFFFF, hi = 0;
    uint32_t sum = 0;
    for (size_t i = 0; i < in_len; i++) {
        uint16_t v = raw[i];
        if (v < lo) lo = v;
        if (v > hi) hi = v;
        sum += v;
    }

    /* 2. Remove DC (the mean of this frame = the mic's bias) */
    float mean = (float)sum / (float)in_len;
    float sq = 0.0f;
    for (size_t i = 0; i < in_len; i++) {
        float x = (float)raw[i] - mean;
        s_signal[i] = x;
        sq += x * x;
    }
    if (stats) {
        stats->raw_min = lo;
        stats->raw_max = hi;
        stats->rms = sqrtf(sq / (float)in_len);
    }

    /*
     * 3 + 4. Decimate (filter, keep every d-th sample) and window, into the
     * real parts of the complex FFT buffer. Samples before the frame start are
     * treated as 0; that start-up transient lasts DECIM_TAPS/d output samples
     * (16 of 512 at d = 4), where the Hann window is almost 0 anyway.
     */
    for (size_t j = 0; j < n; j++) {
        float y;
        if (d == 1) {
            y = s_signal[j];
        } else {
            int centre = (int)(j * d);
            y = 0.0f;
            for (int t = 0; t < DECIM_TAPS; t++) {
                int idx = centre - t;
                if (idx >= 0) y += s_fir[t] * s_signal[idx];
            }
        }
        s_fft[2 * j] = y * s_window[j];
        s_fft[2 * j + 1] = 0.0f;
    }

    /* 5. FFT, magnitude, dB */
    dsps_fft2r_fc32(s_fft, (int)n);
    dsps_bit_rev_fc32(s_fft, (int)n);

    /* |X[k]| of a sine with amplitude A is A * N * window_gain / 2 */
    const float scale = 2.0f / ((float)n * s_window_gain * FULL_SCALE_AMPL);
    for (size_t k = 0; k < n / 2; k++) {
        float re = s_fft[2 * k], im = s_fft[2 * k + 1];
        float a = sqrtf(re * re + im * im) * scale;
        mag_db[k] = a > 1e-7f ? 20.0f * log10f(a) : DB_FLOOR;
    }
    return ESP_OK;
}

void spectrum_deinit(void)
{
    s_ready = false;
    free(s_signal);
    heap_caps_free(s_fft);
    free(s_window);
    s_signal = NULL;
    s_fft = NULL;
    s_window = NULL;
}
