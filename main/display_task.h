/**
 * @file display_task.h
 * @brief Latest audio_frame_t -> bar_model -> frame_gfx -> MAX7219.
 *
 * Runs every APP_DISPLAY_PERIOD_MS whether or not a new frame arrived, so
 * bars keep falling smoothly. Owns max7219 and bar_model.
 */
#pragma once

#include <stdint.h>
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "app_types.h"

/** Create the task; it reads (xQueuePeek/Receive) from @p frames_in. */
esp_err_t display_task_start(QueueHandle_t frames_in);

/** Brightness 0..15. */
void display_task_set_brightness(uint8_t level);
