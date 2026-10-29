/**
 * @file button.h
 * @brief Debounced push button on one GPIO (to GND, internal pull-up).
 *
 * Polled, not interrupt-driven: the input task calls button_poll() every
 * ~10 ms. A press is reported once on release as SHORT or LONG.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    BUTTON_EVT_NONE = 0,
    BUTTON_EVT_SHORT,
    BUTTON_EVT_LONG,
} button_evt_t;

typedef struct {
    int      gpio;
    uint32_t debounce_ms;     /**< e.g. 30 */
    uint32_t long_press_ms;   /**< e.g. 800 */
} button_cfg_t;

typedef struct {
    button_cfg_t cfg;
    bool     stable_pressed;  /**< debounced state */
    bool     last_raw;
    uint32_t last_change_ms;
    uint32_t pressed_at_ms;
} button_t;

/** Configure the GPIO as input with pull-up and reset the state. */
esp_err_t button_init(button_t *b, const button_cfg_t *cfg);

/** Read the pin and run the debounce. Returns an event at most once per press. */
button_evt_t button_poll(button_t *b, uint32_t now_ms);

#ifdef __cplusplus
}
#endif
