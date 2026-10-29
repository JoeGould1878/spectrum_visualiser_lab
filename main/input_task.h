/**
 * @file input_task.h
 * @brief Buttons -> mode / listening changes, saved to NVS.
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
 *
 * MODE button:   short press = next mode (saved), long press = next brightness (saved)
 * LISTEN button: any press = stop / start listening (privacy; not saved —
 *                the device always starts listening, decision log 29/10)
 */
#pragma once

#include "esp_err.h"
#include "settings.h"

/** Start polling. @p initial = the settings main loaded, so the first press steps from them. */
esp_err_t input_task_start(const settings_t *initial);
