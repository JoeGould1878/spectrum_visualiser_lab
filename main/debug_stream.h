/**
 * @file debug_stream.h
 * @brief Machine-readable lines over serial, for logging tests to a file and
 *        plotting in Python (tools/).
 *
 * Plain printf lines (no ESP_LOG prefix) so they are easy to parse; any line
 * not starting with one of these tags is ignored by the tools.
 *
 *   FRAME,<seq>,<t_ms>,<mode>,<status>,<process_us>,<c0_db>,...,<c31_db>
 *   TONE,<seq>,<hz>,<db>
 *   RATE,<measured_sample_rate_hz>
 *   RAW,<n>,<v0>,...,<vn-1>                (bring-up / mic checks only)
 *
 * Bring-up 02 only (printed directly from bringup/02_mic_adc):
 *   RATE_TEST,<requested_hz>,<measured_hz>,<overflows>
 *   STATS,<mean>,<min>,<max>,<rms>          (raw counts; rms after removing the mean)
 *
 * Units: t_ms = ms since boot; c*_db and TONE db = dBFS (0 = full-scale sine);
 * status = frame_status_t bits; mode = app_mode_t number.
 *
 * Capture:  idf.py -p /dev/ttyACM0 monitor | tee docs/evidence/logs/<name>.txt
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "app_types.h"

void debug_stream_set_enabled(bool on);
bool debug_stream_enabled(void);

void debug_stream_frame(const audio_frame_t *f);
void debug_stream_rate(float measured_hz);
void debug_stream_raw(const uint16_t *raw, size_t n);
