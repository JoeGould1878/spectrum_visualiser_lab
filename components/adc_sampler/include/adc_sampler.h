/**
 * @file adc_sampler.h
 * @brief Continuous (DMA) sampling of one ADC1 pin at a fixed rate.
 *
 * Wraps ESP-IDF's ADC continuous-mode driver (esp_adc/adc_continuous.h).
 * Why not analogRead()/adc_oneshot? Aidan's prototype asked for 60 kHz that
 * way and only got ~12 kHz; the continuous driver is clocked by hardware and
 * fills buffers by DMA, so the rate is set by hardware, not by loop timing.
 *
 * ESP32-S3 notes:
 *  - Use an ADC1 pin (GPIO 1-10). ESP-IDF no longer supports ADC2 with DMA.
 *  - The allowed rate range is SOC_ADC_SAMPLE_FREQ_THRES_LOW/HIGH in
 *    soc/soc_caps.h — check it before choosing APP_SAMPLE_RATE_HZ.
 *  - MAX9814 output sits on a ~1.25 V bias with ~2 Vpp max, so it needs the
 *    attenuation setting that covers about 0-2.5 V.
 *
 * Measure the real rate (adc_sampler_measured_rate_hz) — never trust the
 * requested one. That is test "Real sample rate" in docs/PLAN.md.
 */
#pragma once

#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int gpio;                  /**< ADC1-capable pin, e.g. 1 */
    uint32_t sample_rate_hz;   /**< requested rate, e.g. 40000 */
    size_t frame_len;          /**< samples per adc_sampler_read() call */
} adc_sampler_cfg_t;

/** Create the continuous-mode driver for one channel. Does not start it. */
esp_err_t adc_sampler_init(const adc_sampler_cfg_t *cfg);

/** Start / stop conversions (stop = "not listening": no audio is captured). */
esp_err_t adc_sampler_start(void);
esp_err_t adc_sampler_stop(void);

/**
 * Block until @p n raw samples (0..4095) have been collected, in time order.
 * @return ESP_OK, ESP_ERR_TIMEOUT, or ESP_ERR_INVALID_STATE if not started.
 */
esp_err_t adc_sampler_read(uint16_t *out, size_t n, uint32_t timeout_ms);

/** Samples per second actually delivered since start (counted, not assumed). */
float adc_sampler_measured_rate_hz(void);

/** Free the driver. */
void adc_sampler_deinit(void);

#ifdef __cplusplus
}
#endif
