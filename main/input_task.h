/**
 * @file input_task.h
 * @brief Buttons -> mode / listening changes, saved to NVS.
 *
 * MODE button:   short press = next mode (saved), long press = next brightness
 * LISTEN button: short press = stop / start listening (privacy)
 * (Mapping is a proposal — record the final one in the decision log.)
 */
#pragma once

#include "esp_err.h"

esp_err_t input_task_start(void);
