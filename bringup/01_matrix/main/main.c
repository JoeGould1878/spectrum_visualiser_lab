/**
 * @file main.c
 * @brief Bring-up 01 — MAX7219 matrix.
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 *
 * Steps (see bringup/README.md for wiring and what to record):
 *   1. Hardware test mode for 3 s -> every LED lit?
 *   2. Raw single bits, no frame_gfx: chip 0 / row register 0 / bit 7, then
 *      bit 0, then row register 7 / bit 7 -> which chip, which corner? (photo)
 *   3. Orientation sweep: all 16 frame_orient_t combinations, 4 s each, showing
 *      a staircase. The right one rises smoothly from bottom-left to top-right.
 *      Note its number from the serial log, copy the flags into main/app_config.h.
 *   4. Soak: staircase with the app_config.h orientation, rewritten at the real
 *      display rate (40 fps) for 5 min -> any random pixels? (3.3 V logic)
 *      Logs average write time for the latency budget.
 */
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "max7219.h"
#include "frame_gfx.h"
#include "app_config.h"

#define SWEEP_SHOW_MS   4000
#define SOAK_MINUTES    5

static const char *TAG = "bringup01";
static max7219_handle_t s_disp;

static void raw_bit(int dev, int reg, int bit, const char *what)
{
    uint8_t rows[APP_MAX7219_DEVICES * 8] = {0};
    rows[dev * 8 + reg] = (uint8_t)(1u << bit);
    ESP_LOGI(TAG, "STEP 2: %s (chip %d, row register %d, bit %d)", what, dev, reg, bit);
    ESP_ERROR_CHECK(max7219_write_all(s_disp, rows));
    vTaskDelay(pdMS_TO_TICKS(4000));
}

static void staircase(frame_t *f)
{
    frame_clear(f);
    for (int x = 0; x < FRAME_COLS; x++) frame_draw_bar(f, x, x / 4 + 1);
}

static void show(const frame_t *f, const frame_orient_t *o)
{
    uint8_t rows[APP_MAX7219_DEVICES * 8];
    frame_to_device_rows(f, o, APP_MAX7219_DEVICES, rows);
    ESP_ERROR_CHECK(max7219_write_all(s_disp, rows));
}

void app_main(void)
{
    max7219_cfg_t cfg = {
        .host = APP_MAX7219_HOST,
        .pin_din = APP_PIN_MAX7219_DIN,
        .pin_clk = APP_PIN_MAX7219_CLK,
        .pin_cs = APP_PIN_MAX7219_CS,
        .n_devices = APP_MAX7219_DEVICES,
        .clock_hz = APP_MAX7219_CLOCK_HZ,
    };
    ESP_ERROR_CHECK(max7219_init(&cfg, &s_disp));

    /* 1. Hardware test mode */
    ESP_LOGI(TAG, "STEP 1: test mode, all LEDs should be on");
    ESP_ERROR_CHECK(max7219_test_mode(s_disp, true));
    vTaskDelay(pdMS_TO_TICKS(3000));
    ESP_ERROR_CHECK(max7219_test_mode(s_disp, false));
    ESP_ERROR_CHECK(max7219_set_intensity(s_disp, APP_BRIGHTNESS_DEFAULT));
    ESP_ERROR_CHECK(max7219_clear(s_disp));

    /* 2. Raw bits: where does the chip's own (row, bit) grid sit physically? */
    raw_bit(0, 0, 7, "A");
    raw_bit(0, 0, 0, "B");
    raw_bit(0, 7, 7, "C");

    /* 3. Orientation sweep */
    frame_t f;
    staircase(&f);
    ESP_LOGI(TAG, "STEP 3: orientation sweep. Correct = staircase rising left->right from the bottom");
    for (int k = 0; k < 16; k++) {
        frame_orient_t o = {
            .reverse_devices = k & 1,
            .flip_x = (k >> 1) & 1,
            .flip_y = (k >> 2) & 1,
            .transpose = (k >> 3) & 1,
        };
        ESP_LOGI(TAG, "ORIENT %2d: REVERSE_DEVICES=%d FLIP_X=%d FLIP_Y=%d TRANSPOSE=%d",
                 k, o.reverse_devices, o.flip_x, o.flip_y, o.transpose);
        show(&f, &o);
        vTaskDelay(pdMS_TO_TICKS(SWEEP_SHOW_MS));
    }

    /* 4. Soak with the orientation from app_config.h */
    const frame_orient_t orient = {
        .reverse_devices = APP_ORIENT_REVERSE_DEVICES,
        .flip_x = APP_ORIENT_FLIP_X,
        .flip_y = APP_ORIENT_FLIP_Y,
        .transpose = APP_ORIENT_TRANSPOSE,
    };
    ESP_LOGI(TAG, "STEP 4: soak %d min at %d ms/frame, SPI %d Hz, app_config orientation %d%d%d%d",
             SOAK_MINUTES, APP_DISPLAY_PERIOD_MS, APP_MAX7219_CLOCK_HZ,
             orient.reverse_devices, orient.flip_x, orient.flip_y, orient.transpose);

    int64_t start = esp_timer_get_time();
    int64_t write_us_total = 0, write_us_max = 0;
    uint32_t frames = 0;
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        int64_t t0 = esp_timer_get_time();
        show(&f, &orient);
        int64_t dt = esp_timer_get_time() - t0;
        write_us_total += dt;
        if (dt > write_us_max) write_us_max = dt;
        frames++;

        if (frames % (10000 / APP_DISPLAY_PERIOD_MS) == 0) {   /* every ~10 s */
            int elapsed_s = (int)((esp_timer_get_time() - start) / 1000000);
            ESP_LOGI(TAG, "SOAK t=%ds frames=%lu write_avg=%lldus write_max=%lldus%s",
                     elapsed_s, (unsigned long)frames, write_us_total / frames, write_us_max,
                     elapsed_s >= SOAK_MINUTES * 60 ? "  (soak time reached)" : "");
        }
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(APP_DISPLAY_PERIOD_MS));
    }
}
