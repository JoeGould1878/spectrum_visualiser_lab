/**
 * @file debug_stream.c
 * @brief Serial debug lines — implementation.
 *
 * Author: Joe Gould, with Claude (Anthropic) writing the implementation
 */
#include <stdio.h>
#include "debug_stream.h"
#include "app_config.h"

static volatile bool s_enabled = APP_DEBUG_STREAM_DEFAULT;

void debug_stream_set_enabled(bool on) { s_enabled = on; }
bool debug_stream_enabled(void) { return s_enabled; }

void debug_stream_frame(const audio_frame_t *f)
{
    if (!s_enabled) return;
    printf("FRAME,%lu,%lld,%d,%lu,%lu", (unsigned long)f->seq, f->t_us / 1000, (int)f->mode,
           (unsigned long)f->status, (unsigned long)f->process_us);
    for (int c = 0; c < f->cols; c++) printf(",%.1f", f->col_db[c]);
    printf("\n");
    if (f->tone.valid) printf("TONE,%lu,%.1f,%.1f\n", (unsigned long)f->seq, f->tone.hz, f->tone.db);
}

void debug_stream_rate(float measured_hz)
{
    if (!s_enabled) return;
    printf("RATE,%.0f\n", measured_hz);
}

void debug_stream_raw(const uint16_t *raw, size_t n)
{
    if (!s_enabled) return;
    printf("RAW,%u", (unsigned)n);
    for (size_t i = 0; i < n; i++) printf(",%u", raw[i]);
    printf("\n");
}
