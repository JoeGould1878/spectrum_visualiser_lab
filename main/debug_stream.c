/**
 * @file debug_stream.c
 * @brief Serial debug lines — implementation.
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 */
#include <stdio.h>
#include "debug_stream.h"
#include "app_config.h"

static volatile bool s_enabled = APP_DEBUG_STREAM_DEFAULT;

void debug_stream_set_enabled(bool on) { s_enabled = on; }
bool debug_stream_enabled(void) { return s_enabled; }

/*
 * Each line is built in a buffer and printed with one call: audio_task and
 * display_task print from different cores, and several printf calls per line
 * could interleave mid-line.
 */
void debug_stream_frame(const audio_frame_t *f)
{
    if (!s_enabled) return;
    char line[64 + BAND_MAP_MAX_COLS * 8];
    int len = snprintf(line, sizeof(line), "FRAME,%lu,%lld,%d,%lu,%lu", (unsigned long)f->seq,
                       f->t_us / 1000, (int)f->mode, (unsigned long)f->status, (unsigned long)f->process_us);
    for (int c = 0; c < f->cols && len < (int)sizeof(line) - 10; c++) {
        len += snprintf(line + len, sizeof(line) - len, ",%.1f", f->col_db[c]);
    }
    printf("%s\n", line);
    if (f->tone.valid) printf("TONE,%lu,%.1f,%.1f\n", (unsigned long)f->seq, f->tone.hz, f->tone.db);
}

void debug_stream_rate(float measured_hz)
{
    if (!s_enabled) return;
    printf("RATE,%.0f\n", measured_hz);
}

void debug_stream_display(float fps, float age_avg_ms, float age_max_ms, uint32_t write_us)
{
    if (!s_enabled) return;
    printf("DISPLAY,%.1f,%.1f,%.1f,%lu\n", fps, age_avg_ms, age_max_ms, (unsigned long)write_us);
}

void debug_stream_raw(const uint16_t *raw, size_t n)
{
    if (!s_enabled) return;
    printf("RAW,%u", (unsigned)n);
    for (size_t i = 0; i < n; i++) printf(",%u", raw[i]);
    printf("\n");
}
