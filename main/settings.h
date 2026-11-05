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

/*
 * Saved: display mode and brightness only. The orientation is fixed in
 * app_config.h (05/11). The NVS namespace is "sv2", so keys saved by older
 * firmware ("spectrum": mode 1/2, orient) are ignored.
 */
typedef struct {
    app_mode_t mode;         /**< APP_MODE_LOG or APP_MODE_LINEAR */
    uint8_t    brightness;   /**< 0..15 */
} settings_t;

/** Initialise NVS (erase and retry if the partition is full or old). */
esp_err_t settings_init(void);

/** Load saved settings; fills defaults if nothing saved yet. A saved mode that
 *  isn't LOG or LINEAR loads as LOG. */
esp_err_t settings_load(settings_t *out);

/** Save settings (only call on a change — flash has limited write cycles). */
esp_err_t settings_save(const settings_t *s);
