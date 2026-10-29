/**
 * @file audio_task.c
 * @brief Audio pipeline task — implementation.
 *
 * Author: Joe Gould, with Claude (Anthropic) writing the implementation
 *
 * Frames are back to back (no overlap): at 40 kHz and N = 1024 one frame is
 * 25.6 ms of audio, so ~39 analysed frames per second (R4 needs >= 20).
 */
#include <math.h>
#include <stdatomic.h>
#include <string.h>
#include "audio_task.h"
#include "app_config.h"
#include "adc_sampler.h"
#include "spectrum.h"
#include "band_map.h"
#include "tone_finder.h"
#include "frame_gfx.h"
#include "debug_stream.h"
#include "esp_log.h"
#include "esp_timer.h"

static const char *TAG = "audio";

#define MAX_INPUT_LEN  2048   /* max of APP_FFT_N * 1 and APP_FFT_N_BASS * APP_DECIMATE_BASS */
#define MAX_BINS       (APP_FFT_N / 2)

_Static_assert(APP_FFT_N * APP_DECIMATE_FULL <= MAX_INPUT_LEN, "raise MAX_INPUT_LEN");
_Static_assert(APP_FFT_N_BASS * APP_DECIMATE_BASS <= MAX_INPUT_LEN, "raise MAX_INPUT_LEN");
_Static_assert(APP_FFT_N_BASS <= APP_FFT_N, "MAX_BINS assumes the full-mode FFT is the biggest");

static QueueHandle_t s_out;
static atomic_int s_req_mode;
static atomic_bool s_req_listening = true;

/* Owned by the task */
static app_mode_t s_mode = APP_MODE_COUNT;   /* nothing configured yet */
static band_map_t s_map;
static int s_tone_min_bin;
static uint16_t s_raw[MAX_INPUT_LEN];
static float s_bins[MAX_BINS];

typedef struct {
    size_t fft_n;
    int decimate;
    band_map_mode_t map_mode;
    float f_min, f_max;
} mode_setup_t;

static mode_setup_t setup_for(app_mode_t m)
{
    switch (m) {
    case APP_MODE_BASS_VOICE:
        return (mode_setup_t){APP_FFT_N_BASS, APP_DECIMATE_BASS, BAND_MAP_HYBRID_LOG, APP_BASS_F_MIN_HZ, APP_BASS_F_MAX_HZ};
    case APP_MODE_LINEAR:
        return (mode_setup_t){APP_FFT_N, APP_DECIMATE_FULL, BAND_MAP_LINEAR, APP_LINEAR_F_MIN_HZ, APP_LINEAR_F_MAX_HZ};
    case APP_MODE_FULL:
    case APP_MODE_TONE_FINDER:
    default:
        return (mode_setup_t){APP_FFT_N, APP_DECIMATE_FULL, BAND_MAP_HYBRID_LOG, APP_FULL_F_MIN_HZ, APP_FULL_F_MAX_HZ};
    }
}

static esp_err_t configure(app_mode_t m)
{
    mode_setup_t su = setup_for(m);
    spectrum_cfg_t scfg = {
        .fft_n = su.fft_n,
        .sample_rate_hz = APP_SAMPLE_RATE_ACTUAL_HZ,
        .decimate = su.decimate,
        .use_window = APP_USE_WINDOW,
    };
    esp_err_t err = spectrum_init(&scfg);
    if (err != ESP_OK) return err;

    band_map_cfg_t mcfg = {
        .mode = su.map_mode,
        .cols = APP_DISPLAY_COLS,
        .f_min_hz = su.f_min,
        .f_max_hz = su.f_max,
        .bin_hz = spectrum_bin_hz(),
        .n_bins = (int)spectrum_n_bins(),
    };
    if (band_map_build(&s_map, &mcfg) != 0) {
        ESP_LOGE(TAG, "band_map_build failed for mode %d (range vs bins/Nyquist?)", m);
        return ESP_ERR_INVALID_ARG;
    }
    s_tone_min_bin = (int)ceilf(APP_TONE_F_MIN_HZ / spectrum_bin_hz());
    s_mode = m;
    ESP_LOGI(TAG, "mode %d: %u-pt FFT, decimate %d, %.2f Hz bins, %s %.0f-%.0f Hz",
             m, (unsigned)su.fft_n, su.decimate, spectrum_bin_hz(),
             su.map_mode == BAND_MAP_LINEAR ? "linear" : "hybrid log", su.f_min, su.f_max);
    return ESP_OK;
}

static uint32_t status_flags(const spectrum_stats_t *st, const float *col_db, int n_bins)
{
    uint32_t s = 0;
    if (st->rms < APP_SILENCE_RMS) s |= FRAME_STATUS_SILENT;
    if (st->raw_min <= APP_CLIP_MARGIN || st->raw_max >= 4095 - APP_CLIP_MARGIN) s |= FRAME_STATUS_CLIPPING;

    /* Is the loudest thing outside the displayed range? (Only catches energy up to
     * Nyquist — anything above Nyquist has already folded back; that's R6 / the RC filter.) */
    float in_max = -1000.0f, above_max = -1000.0f;
    for (int c = 0; c < s_map.cols; c++) if (col_db[c] > in_max) in_max = col_db[c];
    for (int k = s_map.last_bin[s_map.cols - 1] + 1; k < n_bins; k++) if (s_bins[k] > above_max) above_max = s_bins[k];
    if (above_max > APP_TONE_MIN_DB && above_max > in_max - APP_ABOVE_RANGE_MARGIN_DB) s |= FRAME_STATUS_ABOVE_RANGE;
    return s;
}

static void audio_task(void *arg)
{
    adc_sampler_cfg_t acfg = { .gpio = APP_PIN_MIC, .sample_rate_hz = APP_SAMPLE_RATE_HZ, .frame_len = MAX_INPUT_LEN };
    ESP_ERROR_CHECK(adc_sampler_init(&acfg));

    uint32_t seq = 0;
    bool listening = false;
    uint32_t last_ovf = 0;
    int64_t next_rate_log = esp_timer_get_time() + 1000000;

    for (;;) {
        app_mode_t want = (app_mode_t)atomic_load(&s_req_mode);
        if (want != s_mode && configure(want) != ESP_OK) {
            ESP_LOGE(TAG, "could not configure mode %d, falling back to full", want);
            atomic_store(&s_req_mode, APP_MODE_FULL);
            ESP_ERROR_CHECK(configure(APP_MODE_FULL));
        }

        bool want_listen = atomic_load(&s_req_listening);
        if (want_listen != listening) {
            ESP_ERROR_CHECK(want_listen ? adc_sampler_start() : adc_sampler_stop());
            listening = want_listen;
            ESP_LOGI(TAG, "listening %s", listening ? "ON" : "OFF");
        }

        audio_frame_t f = { .seq = seq++, .mode = s_mode, .cols = s_map.cols, .tone_col = -1 };
        if (!listening) {
            /* No audio captured: send an empty frame so the display shows the state. */
            for (int c = 0; c < f.cols; c++) f.col_db[c] = -140.0f;
            f.status = FRAME_STATUS_NOT_LISTENING;
            f.t_us = esp_timer_get_time();
            xQueueOverwrite(s_out, &f);
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }

        esp_err_t err = adc_sampler_read(s_raw, spectrum_input_len(), 1000);
        if (err != ESP_OK) {
            ESP_LOGW(TAG, "adc read: %s", esp_err_to_name(err));
            continue;
        }
        f.t_us = esp_timer_get_time();

        spectrum_stats_t st;
        int n_bins = (int)spectrum_n_bins();
        ESP_ERROR_CHECK(spectrum_compute(s_raw, s_bins, &st));
        band_map_apply(&s_map, s_bins, f.col_db);
        f.tone = tone_find(s_bins, n_bins, spectrum_bin_hz(), s_tone_min_bin, APP_TONE_MIN_DB);
        if (f.tone.valid) f.tone_col = band_map_column_for_hz(&s_map, f.tone.hz);
        f.status = status_flags(&st, f.col_db, n_bins);
        f.process_us = (uint32_t)(esp_timer_get_time() - f.t_us);

        xQueueOverwrite(s_out, &f);
        if (f.seq % APP_DEBUG_EVERY_N_FRAMES == 0) debug_stream_frame(&f);

        int64_t now = esp_timer_get_time();
        if (now >= next_rate_log) {
            next_rate_log = now + 1000000;
            debug_stream_rate(adc_sampler_measured_rate_hz());
            uint32_t ovf = adc_sampler_overflows();
            if (ovf != last_ovf) {
                ESP_LOGW(TAG, "ADC buffer overflowed %lu times so far (gaps in audio): "
                         "processing or serial output too slow", (unsigned long)ovf);
                last_ovf = ovf;
            }
        }
    }
}

esp_err_t audio_task_start(QueueHandle_t frames_out, app_mode_t initial_mode)
{
    s_out = frames_out;
    atomic_store(&s_req_mode, initial_mode);
    BaseType_t ok = xTaskCreatePinnedToCore(audio_task, "audio", APP_AUDIO_TASK_STACK, NULL,
                                            APP_AUDIO_TASK_PRIO, NULL, APP_AUDIO_TASK_CORE);
    return ok == pdPASS ? ESP_OK : ESP_ERR_NO_MEM;
}

void audio_task_set_mode(app_mode_t mode)
{
    if (mode < APP_MODE_COUNT) atomic_store(&s_req_mode, mode);
}

void audio_task_set_listening(bool on)
{
    atomic_store(&s_req_listening, on);
}
