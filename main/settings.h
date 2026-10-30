/**
 * @file settings.h
 * @brief User settings kept in NVS flash so they survive a reset (R8).
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
 */
#pragma once

#include <stdint.h>
#include "esp_err.h"
#include "app_types.h"

typedef struct {
    app_mode_t mode;
    uint8_t    brightness;   /**< 0..15 */
    uint8_t    orient;       /**< 0..15, display orientation k (see APP_ORIENT_DEFAULT_K) */
} settings_t;

/** Initialise NVS (erase and retry if the partition is full or old). */
esp_err_t settings_init(void);

/** Load saved settings; fills defaults if nothing saved yet. */
esp_err_t settings_load(settings_t *out);

/** Save settings (only call on a change — flash has limited write cycles). */
esp_err_t settings_save(const settings_t *s);
