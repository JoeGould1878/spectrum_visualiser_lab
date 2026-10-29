/**
 * @file main.c
 * @brief Start-up order only — the work happens in the tasks.
 *
 * Spectrum Visualiser — Mini-Challenge 2 (CDIO)
 * Author: Joe Gould, with Claude (Anthropic) writing the implementation
 * Sources and credits: see README.md
 *
 * Start-up order:
 *   1. settings_init(), settings_load()
 *   2. create the 1-slot audio_frame_t queue
 *   3. display_task_start()  — so the display shows something early
 *   4. audio_task_start()    — with the saved mode
 *   5. input_task_start()
 */
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "esp_log.h"
#include "app_config.h"
#include "app_types.h"
#include "settings.h"
#include "audio_task.h"
#include "display_task.h"
#include "input_task.h"

static const char *TAG = "main";

void app_main(void)
{
    /* Settings in every log, so each evidence file says how it was made */
    ESP_LOGI(TAG, "config: rate req %d / actual %d Hz, N %d (bass %d, decim %d), window %d, "
             "full %.0f-%.0f Hz, floor %.1f dB, %.1f dB/row, SPI %d Hz",
             APP_SAMPLE_RATE_HZ, APP_SAMPLE_RATE_ACTUAL_HZ, APP_FFT_N, APP_FFT_N_BASS, APP_DECIMATE_BASS,
             APP_USE_WINDOW, APP_FULL_F_MIN_HZ, APP_FULL_F_MAX_HZ, APP_FLOOR_DB, APP_DB_PER_ROW,
             APP_MAX7219_CLOCK_HZ);

    ESP_ERROR_CHECK(settings_init());
    settings_t s;
    ESP_ERROR_CHECK(settings_load(&s));

    QueueHandle_t frames = xQueueCreate(1, sizeof(audio_frame_t));
    configASSERT(frames);

    ESP_ERROR_CHECK(display_task_start(frames));
    display_task_set_brightness(s.brightness);
    ESP_ERROR_CHECK(audio_task_start(frames, s.mode));
    ESP_ERROR_CHECK(input_task_start(&s));
    ESP_LOGI(TAG, "running: mode %d, brightness %u", s.mode, s.brightness);
}
