/**
 * @file input_task.c
 * @brief Button task — implementation.
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 *
 * Owns both buttons. Changes are passed on through audio_task_set_mode(),
 * audio_task_set_listening(), display_task_set_brightness() and
 * display_task_set_orientation(); mode, brightness and orientation are saved
 * to NVS only when they change.
 *
 *   MODE   short: next mode        long: next brightness
 *   LISTEN short: stop/start       long: next display orientation (k 0..15)
 */
#include "input_task.h"
#include "app_config.h"
#include "audio_task.h"
#include "display_task.h"
#include "button.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "input";

static const uint8_t BRIGHTNESS_STEPS[] = APP_BRIGHTNESS_STEPS;
#define N_STEPS (sizeof(BRIGHTNESS_STEPS) / sizeof(BRIGHTNESS_STEPS[0]))

static settings_t s_settings;
static button_t s_btn_mode, s_btn_listen;

/* Next step above the current brightness, wrapping to the dimmest. */
static uint8_t next_brightness(uint8_t now)
{
    for (size_t i = 0; i < N_STEPS; i++) {
        if (BRIGHTNESS_STEPS[i] > now) return BRIGHTNESS_STEPS[i];
    }
    return BRIGHTNESS_STEPS[0];
}

static void save(void)
{
    esp_err_t err = settings_save(&s_settings);
    if (err != ESP_OK) ESP_LOGW(TAG, "save failed: %s", esp_err_to_name(err));
}

static void input_task(void *arg)
{
    bool listening = true;   /* matches audio_task's start-up state */
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(APP_INPUT_PERIOD_MS));
        uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);

        switch (button_poll(&s_btn_mode, now_ms)) {
        case BUTTON_EVT_SHORT:
            s_settings.mode = (app_mode_t)((s_settings.mode + 1) % APP_MODE_COUNT);
            if (!APP_SHOW_TONE_MODE && s_settings.mode == APP_MODE_TONE_FINDER)
                s_settings.mode = (app_mode_t)((s_settings.mode + 1) % APP_MODE_COUNT);
            audio_task_set_mode(s_settings.mode);
            save();
            ESP_LOGI(TAG, "mode -> %d", s_settings.mode);
            break;
        case BUTTON_EVT_LONG:
            s_settings.brightness = next_brightness(s_settings.brightness);
            display_task_set_brightness(s_settings.brightness);
            save();
            ESP_LOGI(TAG, "brightness -> %u", s_settings.brightness);
            break;
        default:
            break;
        }

        switch (button_poll(&s_btn_listen, now_ms)) {
        case BUTTON_EVT_SHORT:
            listening = !listening;
            audio_task_set_listening(listening);
            ESP_LOGI(TAG, "listening -> %s", listening ? "ON" : "OFF");
            break;
        case BUTTON_EVT_LONG:
            s_settings.orient = (uint8_t)((s_settings.orient + 1) & 15u);
            display_task_set_orientation(s_settings.orient);
            save();
            ESP_LOGI(TAG, "orientation -> %u", s_settings.orient);
            break;
        default:
            break;
        }
    }
}

esp_err_t input_task_start(const settings_t *initial)
{
    ESP_RETURN_ON_FALSE(initial, ESP_ERR_INVALID_ARG, TAG, "null settings");
    s_settings = *initial;
    button_cfg_t mode_cfg = { .gpio = APP_PIN_BTN_MODE, .debounce_ms = APP_BTN_DEBOUNCE_MS, .long_press_ms = APP_BTN_LONG_MS };
    button_cfg_t listen_cfg = { .gpio = APP_PIN_BTN_LISTEN, .debounce_ms = APP_BTN_DEBOUNCE_MS, .long_press_ms = APP_BTN_LONG_MS };
    ESP_RETURN_ON_ERROR(button_init(&s_btn_mode, &mode_cfg), TAG, "mode button");
    ESP_RETURN_ON_ERROR(button_init(&s_btn_listen, &listen_cfg), TAG, "listen button");
    BaseType_t ok = xTaskCreatePinnedToCore(input_task, "input", APP_INPUT_TASK_STACK, NULL,
                                            APP_INPUT_TASK_PRIO, NULL, APP_INPUT_TASK_CORE);
    return ok == pdPASS ? ESP_OK : ESP_ERR_NO_MEM;
}
