/**
 * @file main.c
 * @brief Bring-up 02 — electret mic + NPN preamp (or generator) -> continuous ADC.
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 *
 * Steps (see bringup/README.md for wiring and what to record):
 *   1. Rate sweep: for each requested rate, run 3 s while reading continuously
 *      and print  RATE_TEST,<requested>,<measured>,<overflows>
 *   2. Then at APP_SAMPLE_RATE_HZ, forever, once a second:
 *        RATE,<measured Hz>
 *        STATS,<mean>,<min>,<max>,<rms>      (raw counts, rms after removing mean)
 *        RAW,<n>,<v0>,...,<vn-1>              (one contiguous frame)
 *      Record quiet room / talking / clap / phone 1 kHz tone through the
 *      preamp (and a generator tone through the test input).
 */
#include <math.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "adc_sampler.h"
#include "app_config.h"

#define RAW_N           1024
#define SWEEP_SECONDS   3

static const char *TAG = "bringup02";
static uint16_t s_buf[RAW_N];

static const uint32_t SWEEP_RATES[] = {20000, 40000, 48000, 60000, 80000, 83333};

static void run_rate_test(uint32_t rate)
{
    adc_sampler_cfg_t cfg = { .gpio = APP_PIN_MIC, .sample_rate_hz = rate, .frame_len = RAW_N };
    ESP_ERROR_CHECK(adc_sampler_init(&cfg));
    ESP_ERROR_CHECK(adc_sampler_start());
    int64_t end = esp_timer_get_time() + SWEEP_SECONDS * 1000000LL;
    while (esp_timer_get_time() < end) {
        ESP_ERROR_CHECK(adc_sampler_read(s_buf, RAW_N, 1000));
    }
    printf("RATE_TEST,%lu,%.0f,%lu\n", (unsigned long)rate,
           adc_sampler_measured_rate_hz(), (unsigned long)adc_sampler_overflows());
    adc_sampler_deinit();
}

void app_main(void)
{
    ESP_LOGI(TAG, "STEP 1: rate sweep, %d s per rate", SWEEP_SECONDS);
    for (size_t i = 0; i < sizeof(SWEEP_RATES) / sizeof(SWEEP_RATES[0]); i++) {
        run_rate_test(SWEEP_RATES[i]);
    }

    ESP_LOGI(TAG, "STEP 2: streaming at %d Hz requested, one RAW frame per second", APP_SAMPLE_RATE_HZ);
    adc_sampler_cfg_t cfg = { .gpio = APP_PIN_MIC, .sample_rate_hz = APP_SAMPLE_RATE_HZ, .frame_len = RAW_N };
    ESP_ERROR_CHECK(adc_sampler_init(&cfg));
    ESP_ERROR_CHECK(adc_sampler_start());

    int64_t next_print = esp_timer_get_time() + 1000000;
    for (;;) {
        /* Keep reading so the pool never overflows; print one frame a second. */
        ESP_ERROR_CHECK(adc_sampler_read(s_buf, RAW_N, 1000));
        if (esp_timer_get_time() < next_print) continue;
        next_print += 1000000;

        double sum = 0;
        uint16_t lo = 4095, hi = 0;
        for (int i = 0; i < RAW_N; i++) {
            sum += s_buf[i];
            if (s_buf[i] < lo) lo = s_buf[i];
            if (s_buf[i] > hi) hi = s_buf[i];
        }
        double mean = sum / RAW_N, sq = 0;
        for (int i = 0; i < RAW_N; i++) sq += (s_buf[i] - mean) * (s_buf[i] - mean);

        printf("RATE,%.0f\n", adc_sampler_measured_rate_hz());
        printf("STATS,%.1f,%u,%u,%.1f\n", mean, lo, hi, sqrt(sq / RAW_N));
        printf("RAW,%d", RAW_N);
        for (int i = 0; i < RAW_N; i++) printf(",%u", s_buf[i]);
        /* Printing ~5 KB takes longer than the pool lasts, so overflows here are
         * expected and harmless: each RAW frame was captured in one piece before printing. */
        printf("\n");
    }
}
