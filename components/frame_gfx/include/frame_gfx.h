/**
 * @file frame_gfx.h
 * @brief 32 x 8 picture in memory: bars, peak dots, status pixels, small text,
 *        and conversion to MAX7219 rows. Pure C — no ESP-IDF.
 *
 * Coordinates: x = column 0..31 (0 = lowest frequency, left),
 *              y = row 0..7     (0 = bottom).
 * A frame stores one byte per column, bit y = pixel (x, y).
 *
 * frame_gfx_to_device_rows() is the ONLY place that knows how the 4-in-1
 * module is mounted (which chip is leftmost, whether rows/columns are flipped).
 * Bring-up 01 finds the right orientation; record it in app_config.h.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define FRAME_COLS 32
#define FRAME_ROWS 8

typedef struct {
    uint8_t col[FRAME_COLS];   /**< bit y of col[x] = pixel (x, y) */
} frame_t;

/** How the module is mounted; options found at bring-up 01. */
typedef struct {
    bool reverse_devices;      /**< chip 0 (nearest DIN) is on the right */
    bool flip_x;               /**< mirror left-right within each chip */
    bool flip_y;               /**< mirror up-down within each chip */
    bool transpose;            /**< chip "rows" are our columns */
} frame_orient_t;

/** Status pixels for the "can I trust it?" row (layout decided in Design). */
typedef enum {
    FRAME_STATUS_SILENT        = 1u << 0,
    FRAME_STATUS_CLIPPING      = 1u << 1,
    FRAME_STATUS_ABOVE_RANGE   = 1u << 2,   /**< strong energy above the displayed range */
    FRAME_STATUS_NOT_LISTENING = 1u << 3,
} frame_status_t;

void frame_clear(frame_t *f);
void frame_set_pixel(frame_t *f, int x, int y, bool on);
bool frame_get_pixel(const frame_t *f, int x, int y);

/** Fill column x from row 0 up to height-1 (height 0..8). */
void frame_draw_bar(frame_t *f, int x, int height);

/** Light a single pixel at row (peak_row - 1); 0 = no dot. */
void frame_draw_peak(frame_t *f, int x, int peak_row);

/** Draw status flags (frame_status_t bits) — exact layout TBD. */
void frame_draw_status(frame_t *f, uint32_t status_flags);

/**
 * Draw text in a small font (digits, "Hz", "k" at least), starting at
 * pixel column x_offset (can be negative, for scrolling).
 * @return total width of the text in pixels.
 */
int frame_draw_text(frame_t *f, const char *text, int x_offset);

/**
 * Convert to what max7219_write_all() expects:
 * out[dev * 8 + r] = row r of chip dev (n_devices * 8 bytes).
 */
void frame_to_device_rows(const frame_t *f, const frame_orient_t *orient,
                          int n_devices, uint8_t *out);

/** Print the frame as ASCII art ('#' / '.'), top row first, for laptop tests. */
void frame_print_ascii(const frame_t *f);

#ifdef __cplusplus
}
#endif
