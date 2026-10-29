/**
 * @file display_task.c
 * @brief Display task — implementation.
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 *
 * Every APP_DISPLAY_PERIOD_MS: take the newest audio frame if one arrived,
 * update the bar model (so bars keep falling between frames), draw, write.
 * Owns max7219 and bar_model.
 */
#include <stdatomic.h>
#include <stdio.h>
#include "display_task.h"
#include "app_config.h"
#include "max7219.h"
#include "bar_model.h"
#include "frame_gfx.h"
#include "debug_stream.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"

static const char *TAG = "display";

static QueueHandle_t s_in;
static atomic_uint s_req_brightness = APP_BRIGHTNESS_DEFAULT;

/* Owned by the task */
static max7219_handle_t s_disp;
static bar_model_t s_bars;
static const frame_orient_t s_orient = {
    .reverse_devices = APP_ORIENT_REVERSE_DEVICES,
    .flip_x = APP_ORIENT_FLIP_X,
    .flip_y = APP_ORIENT_FLIP_Y,
    .transpose = APP_ORIENT_TRANSPOSE,
};

static void draw_spectrum(frame_t *fr, const audio_frame_t *a, float dt_s)
{
    bar_model_update(&s_bars, a->col_db, dt_s);
    for (int x = 0; x < a->cols && x < FRAME_COLS; x++) {
        int h = bar_model_height(&s_bars, x);
        frame_draw_bar(fr, x, h);
        int p = bar_model_peak_row(&s_bars, x);
        if (p > h) frame_draw_peak(fr, x, p);   /* a dot inside the bar would be invisible */
    }
}

/*
 * Tone-finder: frequency as digits in rows 1-5, centred, updated only every
 * APP_TONE_DISPLAY_MS so it can be read (no scrolling needed: "20000Hz" is 27 px).
 * Bottom row: one pixel under the column that tone lights in full mode.
 */
static void draw_tone(frame_t *fr, const audio_frame_t *a, int64_t now_us)
{
    static int64_t next_update_us;
    static char text[12] = "---";
    static int marker_col = -1;

    if (now_us >= next_update_us) {
        next_update_us = now_us + APP_TONE_DISPLAY_MS * 1000LL;
        if (a->tone.valid) {
            int hz = (int)(a->tone.hz + 0.5f);
            snprintf(text, sizeof(text), "%dHz", hz);
            marker_col = a->tone_col;
        } else {
            snprintf(text, sizeof(text), "---");
            marker_col = -1;
        }
    }
    frame_t probe;
    frame_clear(&probe);
    int w = frame_draw_text(&probe, text, 0);
    frame_draw_text(fr, text, (FRAME_COLS - w) / 2);
    if (marker_col >= 0) frame_set_pixel(fr, marker_col, 0, true);
}

static void display_task(void *arg)
{
    bar_model_cfg_t bcfg = {
        .rows = FRAME_ROWS,
        .floor_db = APP_FLOOR_DB,
        .db_per_row = APP_DB_PER_ROW,
        .fall_rows_per_s = APP_FALL_ROWS_PER_S,
        .peak_hold_s = APP_PEAK_HOLD_S,
        .peak_fall_rows_per_s = APP_PEAK_FALL_ROWS_PER_S,
    };
    bar_model_init(&s_bars, &bcfg, APP_DISPLAY_COLS);

    audio_frame_t latest = {0};
    bool have_frame = false;
    app_mode_t last_mode = APP_MODE_COUNT;
    unsigned brightness = 0xFF;
    uint8_t rows[APP_MAX7219_DEVICES * 8];

    /* Once-a-second DISPLAY line: refresh rate, frame age, SPI write time */
    uint32_t ticks = 0, new_frames = 0, write_us_max = 0;
    float age_sum_ms = 0, age_max_ms = 0;
    int64_t stats_start = esp_timer_get_time();

    int64_t last_us = esp_timer_get_time();
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(APP_DISPLAY_PERIOD_MS));
        int64_t now = esp_timer_get_time();
        float dt_s = (float)(now - last_us) / 1e6f;
        last_us = now;

        unsigned want_b = atomic_load(&s_req_brightness);
        if (want_b != brightness) {
            max7219_set_intensity(s_disp, (uint8_t)want_b);
            brightness = want_b;
        }

        bool fresh = xQueueReceive(s_in, &latest, 0) == pdTRUE;
        if (fresh) have_frame = true;

        frame_t fr;
        frame_clear(&fr);
        if (have_frame) {
            if (latest.mode != last_mode) {   /* new mode: don't carry old bars over */
                bar_model_init(&s_bars, &bcfg, APP_DISPLAY_COLS);
                last_mode = latest.mode;
            }
            if (latest.status & FRAME_STATUS_NOT_LISTENING) {
                bar_model_init(&s_bars, &bcfg, APP_DISPLAY_COLS);   /* blank, not falling */
            } else if (latest.mode == APP_MODE_TONE_FINDER) {
                draw_tone(&fr, &latest, now);
            } else {
                draw_spectrum(&fr, &latest, dt_s);
            }
            frame_draw_status(&fr, latest.status);
        }

        frame_to_device_rows(&fr, &s_orient, APP_MAX7219_DEVICES, rows);
        int64_t t0 = esp_timer_get_time();
        esp_err_t err = max7219_write_all(s_disp, rows);
        int64_t t1 = esp_timer_get_time();
        if (err != ESP_OK) ESP_LOGW(TAG, "write: %s", esp_err_to_name(err));

        ticks++;
        if ((uint32_t)(t1 - t0) > write_us_max) write_us_max = (uint32_t)(t1 - t0);
        if (fresh) {
            float age_ms = (float)(t1 - latest.t_us) / 1000.0f;
            age_sum_ms += age_ms;
            if (age_ms > age_max_ms) age_max_ms = age_ms;
            new_frames++;
        }
        if (t1 - stats_start >= 1000000) {
            float secs = (float)(t1 - stats_start) / 1e6f;
            debug_stream_display(ticks / secs, new_frames ? age_sum_ms / new_frames : 0.0f,
                                 age_max_ms, write_us_max);
            ticks = new_frames = write_us_max = 0;
            age_sum_ms = age_max_ms = 0;
            stats_start = t1;
        }
    }
}

esp_err_t display_task_start(QueueHandle_t frames_in)
{
    s_in = frames_in;
    max7219_cfg_t cfg = {
        .host = APP_MAX7219_HOST,
        .pin_din = APP_PIN_MAX7219_DIN,
        .pin_clk = APP_PIN_MAX7219_CLK,
        .pin_cs = APP_PIN_MAX7219_CS,
        .n_devices = APP_MAX7219_DEVICES,
        .clock_hz = APP_MAX7219_CLOCK_HZ,
    };
    ESP_RETURN_ON_ERROR(max7219_init(&cfg, &s_disp), TAG, "max7219_init");
    BaseType_t ok = xTaskCreatePinnedToCore(display_task, "display", APP_DISPLAY_TASK_STACK, NULL,
                                            APP_DISPLAY_TASK_PRIO, NULL, APP_DISPLAY_TASK_CORE);
    return ok == pdPASS ? ESP_OK : ESP_ERR_NO_MEM;
}

void display_task_set_brightness(uint8_t level)
{
    atomic_store(&s_req_brightness, level > 15 ? 15 : level);
}
