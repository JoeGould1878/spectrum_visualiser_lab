/**
 * @file display_task.h
 * @brief Latest audio_frame_t -> bar_model -> frame_gfx -> MAX7219.
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
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

/**
 * Display orientation k (0..15, same numbering as bring-up 01). The display
 * shows a test staircase for APP_STAIRCASE_ORIENT_MS so the result can be
 * judged: correct = rising from bottom-left to top-right.
 */
void display_task_set_orientation(uint8_t k);
