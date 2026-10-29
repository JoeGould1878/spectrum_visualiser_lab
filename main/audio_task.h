/**
 * @file audio_task.h
 * @brief Sampling -> spectrum -> columns -> audio_frame_t, on its own core.
 *
 * Loop: adc_sampler_read() a frame, spectrum_compute(), band_map_apply(),
 * tone_find(), set status flags, then xQueueOverwrite() to the display.
 * Owns adc_sampler, spectrum and band_map — nothing else touches them.
 */
#pragma once

#include <stdbool.h>
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "app_types.h"

/** Create the task. @p frames_out is a 1-slot queue of audio_frame_t. */
esp_err_t audio_task_start(QueueHandle_t frames_out, app_mode_t initial_mode);

/** Change mode; the task rebuilds spectrum/band_map before the next frame. */
void audio_task_set_mode(app_mode_t mode);

/** false = stop the ADC (no audio captured at all), true = listen again. */
void audio_task_set_listening(bool on);
