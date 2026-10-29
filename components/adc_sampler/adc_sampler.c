/**
 * @file adc_sampler.c
 * @brief Continuous ADC sampling — implementation.
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 * Credits / sources used: ESP-IDF v6 adc_continuous API documentation and the
 *   examples/peripherals/adc/continuous_read example (handle/config/pattern
 *   setup and the read-then-parse loop follow its structure; rewritten for one
 *   channel, with interrupt-side counters added for rate and overflow checks).
 *
 * Data path: ADC hardware -> DMA -> driver ring buffer ("pool") -> read().
 * The driver delivers results in "conversion frames" of CONV_FRAME_SAMPLES.
 */
#include <stdatomic.h>
#include <string.h>
#include "adc_sampler.h"
#include "esp_adc/adc_continuous.h"
#include "esp_check.h"
#include "esp_timer.h"

static const char *TAG = "adc_sampler";

#define CONV_FRAME_SAMPLES  256                         /* ~6 ms at 40 kHz */
#define CONV_FRAME_BYTES    (CONV_FRAME_SAMPLES * SOC_ADC_DIGI_RESULT_BYTES)
#define POOL_BYTES          (CONV_FRAME_BYTES * 16)     /* ~100 ms of slack at 40 kHz */

/*
 * 12 dB attenuation: the S3 measures roughly 0-3.1 V. The MAX9814 swings
 * 1.25 V +/- 1 V (0.25-2.25 V); 6 dB attenuation only reaches ~1.75 V and
 * would clip the top of every loud waveform.
 */
#define ADC_ATTEN           ADC_ATTEN_DB_12

static adc_continuous_handle_t s_handle;
static adc_unit_t s_unit;
static adc_channel_t s_channel;
static bool s_started;
static int64_t s_start_us;
static atomic_uint_fast32_t s_conv_frames;   /* incremented in ISR */
static atomic_uint_fast32_t s_overflows;     /* incremented in ISR */

static uint8_t s_raw_buf[CONV_FRAME_BYTES];
static adc_continuous_data_t s_parsed[CONV_FRAME_SAMPLES];

static bool IRAM_ATTR on_conv_done(adc_continuous_handle_t h, const adc_continuous_evt_data_t *e, void *u)
{
    atomic_fetch_add(&s_conv_frames, 1);
    return false;
}

static bool IRAM_ATTR on_pool_ovf(adc_continuous_handle_t h, const adc_continuous_evt_data_t *e, void *u)
{
    atomic_fetch_add(&s_overflows, 1);
    return false;
}

esp_err_t adc_sampler_init(const adc_sampler_cfg_t *cfg)
{
    ESP_RETURN_ON_FALSE(cfg, ESP_ERR_INVALID_ARG, TAG, "null cfg");
    ESP_RETURN_ON_FALSE(!s_handle, ESP_ERR_INVALID_STATE, TAG, "already initialised");
    ESP_RETURN_ON_FALSE(cfg->sample_rate_hz >= SOC_ADC_SAMPLE_FREQ_THRES_LOW &&
                        cfg->sample_rate_hz <= SOC_ADC_SAMPLE_FREQ_THRES_HIGH,
                        ESP_ERR_INVALID_ARG, TAG, "rate %lu outside %d..%d Hz",
                        (unsigned long)cfg->sample_rate_hz,
                        SOC_ADC_SAMPLE_FREQ_THRES_LOW, SOC_ADC_SAMPLE_FREQ_THRES_HIGH);

    ESP_RETURN_ON_ERROR(adc_continuous_io_to_channel(cfg->gpio, &s_unit, &s_channel),
                        TAG, "GPIO %d is not an ADC pin", cfg->gpio);
    ESP_RETURN_ON_FALSE(s_unit == ADC_UNIT_1, ESP_ERR_INVALID_ARG, TAG,
                        "GPIO %d is on ADC2; continuous mode needs ADC1 (GPIO 1-10)", cfg->gpio);

    adc_continuous_handle_cfg_t hcfg = {
        .max_store_buf_size = POOL_BYTES,
        .conv_frame_size = CONV_FRAME_BYTES,
        /* If we fall behind and the pool fills, the driver throws away the WHOLE pool
         * (~100 ms) and carries on with fresh data, rather than stalling. The frame
         * being read at that moment then has a gap; adc_sampler_overflows() counts it. */
        .flags.flush_pool = 1,
    };
    ESP_RETURN_ON_ERROR(adc_continuous_new_handle(&hcfg, &s_handle), TAG, "new_handle");

    adc_digi_pattern_config_t pattern = {
        .atten = ADC_ATTEN,
        .channel = s_channel,
        .unit = s_unit,
        .bit_width = SOC_ADC_DIGI_MAX_BITWIDTH,
    };
    adc_continuous_config_t ccfg = {
        .pattern_num = 1,
        .adc_pattern = &pattern,
        .sample_freq_hz = cfg->sample_rate_hz,
        .conv_mode = ADC_CONV_SINGLE_UNIT_1,
    };
    esp_err_t err = adc_continuous_config(s_handle, &ccfg);
    if (err == ESP_OK) {
        adc_continuous_evt_cbs_t cbs = { .on_conv_done = on_conv_done, .on_pool_ovf = on_pool_ovf };
        err = adc_continuous_register_event_callbacks(s_handle, &cbs, NULL);
    }
    if (err != ESP_OK) {
        adc_continuous_deinit(s_handle);
        s_handle = NULL;
        ESP_RETURN_ON_ERROR(err, TAG, "config");
    }

    ESP_LOGI(TAG, "GPIO %d = ADC1 ch %d, requested %lu Hz, 12 dB atten",
             cfg->gpio, (int)s_channel, (unsigned long)cfg->sample_rate_hz);
    return ESP_OK;
}

esp_err_t adc_sampler_start(void)
{
    ESP_RETURN_ON_FALSE(s_handle, ESP_ERR_INVALID_STATE, TAG, "not initialised");
    if (s_started) return ESP_OK;
    atomic_store(&s_conv_frames, 0);
    atomic_store(&s_overflows, 0);
    s_start_us = esp_timer_get_time();
    ESP_RETURN_ON_ERROR(adc_continuous_start(s_handle), TAG, "start");
    s_started = true;
    return ESP_OK;
}

esp_err_t adc_sampler_stop(void)
{
    ESP_RETURN_ON_FALSE(s_handle, ESP_ERR_INVALID_STATE, TAG, "not initialised");
    if (!s_started) return ESP_OK;
    ESP_RETURN_ON_ERROR(adc_continuous_stop(s_handle), TAG, "stop");
    s_started = false;
    /* Throw away anything still buffered: nothing captured before "stop" survives. */
    adc_continuous_flush_pool(s_handle);
    return ESP_OK;
}

esp_err_t adc_sampler_read(uint16_t *out, size_t n, uint32_t timeout_ms)
{
    ESP_RETURN_ON_FALSE(out, ESP_ERR_INVALID_ARG, TAG, "null out");
    if (!s_started) return ESP_ERR_INVALID_STATE;

    int64_t deadline = esp_timer_get_time() + (int64_t)timeout_ms * 1000;
    size_t got = 0;
    while (got < n) {
        /* Never read more than we still need, so no samples are left over. */
        uint32_t want = (uint32_t)(n - got) * SOC_ADC_DIGI_RESULT_BYTES;
        if (want > CONV_FRAME_BYTES) want = CONV_FRAME_BYTES;

        int64_t left_us = deadline - esp_timer_get_time();
        if (left_us <= 0) return ESP_ERR_TIMEOUT;

        uint32_t len = 0;
        esp_err_t err = adc_continuous_read(s_handle, s_raw_buf, want, &len, (uint32_t)(left_us / 1000) + 1);
        if (err == ESP_ERR_TIMEOUT) return ESP_ERR_TIMEOUT;
        ESP_RETURN_ON_ERROR(err, TAG, "read");

        uint32_t n_parsed = 0;
        ESP_RETURN_ON_ERROR(adc_continuous_parse_data(s_handle, s_raw_buf, len, s_parsed, &n_parsed),
                            TAG, "parse");
        for (uint32_t i = 0; i < n_parsed && got < n; i++) {
            if (s_parsed[i].valid && s_parsed[i].channel == s_channel) {
                out[got++] = (uint16_t)s_parsed[i].raw_data;
            }
        }
    }
    return ESP_OK;
}

float adc_sampler_measured_rate_hz(void)
{
    if (!s_started) return 0.0f;
    int64_t dt_us = esp_timer_get_time() - s_start_us;
    if (dt_us <= 0) return 0.0f;
    uint32_t frames = atomic_load(&s_conv_frames);
    return (float)((double)frames * CONV_FRAME_SAMPLES * 1e6 / (double)dt_us);
}

uint32_t adc_sampler_overflows(void)
{
    return atomic_load(&s_overflows);
}

void adc_sampler_deinit(void)
{
    if (!s_handle) return;
    if (s_started) adc_sampler_stop();
    adc_continuous_deinit(s_handle);
    s_handle = NULL;
}
