/**
 * @file button.c
 * @brief Debounced button — implementation.
 *
 * Author: Joe Gould, with Claude (Anthropic) writing the implementation
 * Credits / sources used: none adapted (time-based debounce: the raw level
 *   must stay the same for debounce_ms before it counts).
 */
#include "button.h"
#include "driver/gpio.h"
#include "esp_check.h"

static const char *TAG = "button";

esp_err_t button_init(button_t *b, const button_cfg_t *cfg)
{
    ESP_RETURN_ON_FALSE(b && cfg, ESP_ERR_INVALID_ARG, TAG, "null arg");
    gpio_config_t io = {
        .pin_bit_mask = 1ULL << cfg->gpio,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&io), TAG, "gpio_config %d", cfg->gpio);
    b->cfg = *cfg;
    b->stable_pressed = false;
    b->last_raw = false;
    b->last_change_ms = 0;
    b->pressed_at_ms = 0;
    return ESP_OK;
}

button_evt_t button_poll(button_t *b, uint32_t now_ms)
{
    bool raw = gpio_get_level(b->cfg.gpio) == 0;   /* pressed = pulled to GND */
    if (raw != b->last_raw) {
        b->last_raw = raw;
        b->last_change_ms = now_ms;
        return BUTTON_EVT_NONE;
    }
    if (raw == b->stable_pressed || now_ms - b->last_change_ms < b->cfg.debounce_ms) {
        return BUTTON_EVT_NONE;
    }

    b->stable_pressed = raw;
    if (raw) {
        b->pressed_at_ms = now_ms;
        return BUTTON_EVT_NONE;
    }
    /* released: report once, by how long it was held */
    return (now_ms - b->pressed_at_ms >= b->cfg.long_press_ms) ? BUTTON_EVT_LONG : BUTTON_EVT_SHORT;
}
