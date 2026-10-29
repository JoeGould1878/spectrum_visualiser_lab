/**
 * @file frame_gfx.c
 * @brief 32 x 8 frame drawing — implementation (pure C).
 *
 * Author: Joe Gould, with Claude (Anthropic) writing the implementation
 * Credits / sources used: 3x5 font drawn by hand for this project.
 */
#include <stdio.h>
#include <string.h>
#include "frame_gfx.h"

/* ---------------- Font ---------------- */

#define GLYPH_W   3
#define GLYPH_H   5
#define GLYPH_GAP 1
#define TEXT_Y0   1   /* bottom row of the text: rows 1..5, centred-ish */

typedef struct {
    char c;
    uint8_t rows[GLYPH_H];   /* top row first; bit 2 = left column */
} glyph_t;

static const glyph_t FONT[] = {
    {'0', {7, 5, 5, 5, 7}}, {'1', {2, 6, 2, 2, 7}}, {'2', {7, 1, 7, 4, 7}},
    {'3', {7, 1, 7, 1, 7}}, {'4', {5, 5, 7, 1, 1}}, {'5', {7, 4, 7, 1, 7}},
    {'6', {7, 4, 7, 5, 7}}, {'7', {7, 1, 1, 1, 1}}, {'8', {7, 5, 7, 5, 7}},
    {'9', {7, 5, 7, 1, 7}}, {'H', {5, 5, 7, 5, 5}}, {'z', {0, 7, 1, 2, 7}},
    {'k', {4, 5, 6, 5, 5}}, {'.', {0, 0, 0, 0, 2}}, {'-', {0, 0, 7, 0, 0}},
    {' ', {0, 0, 0, 0, 0}},
};

static const glyph_t *find_glyph(char c)
{
    for (size_t i = 0; i < sizeof(FONT) / sizeof(FONT[0]); i++) {
        if (FONT[i].c == c) return &FONT[i];
    }
    return &FONT[sizeof(FONT) / sizeof(FONT[0]) - 1];   /* unknown -> space */
}

/* ---------------- Pixels ---------------- */

static bool in_range(int x, int y)
{
    return x >= 0 && x < FRAME_COLS && y >= 0 && y < FRAME_ROWS;
}

void frame_clear(frame_t *f)
{
    memset(f->col, 0, sizeof(f->col));
}

void frame_set_pixel(frame_t *f, int x, int y, bool on)
{
    if (!in_range(x, y)) return;
    if (on) f->col[x] |= (uint8_t)(1u << y);
    else    f->col[x] &= (uint8_t)~(1u << y);
}

bool frame_get_pixel(const frame_t *f, int x, int y)
{
    if (!in_range(x, y)) return false;
    return (f->col[x] >> y) & 1u;
}

void frame_draw_bar(frame_t *f, int x, int height)
{
    if (x < 0 || x >= FRAME_COLS || height <= 0) return;
    if (height > FRAME_ROWS) height = FRAME_ROWS;
    f->col[x] |= (uint8_t)((1u << height) - 1u);
}

void frame_draw_peak(frame_t *f, int x, int peak_row)
{
    if (peak_row <= 0) return;
    if (peak_row > FRAME_ROWS) peak_row = FRAME_ROWS;
    frame_set_pixel(f, x, peak_row - 1, true);
}

/*
 * Status area = top two rows of the rightmost four columns (the 5.5-8 kHz
 * columns, which rarely reach full height). While ANY flag is set, that area is
 * cleared first, so a status pixel can never be mistaken for the top of a bar;
 * row 6 stays dark as a gap. Flag bit i lights the top-row pixel of column 31 - i.
 * With no flags set, bars draw there normally.
 */
void frame_draw_status(frame_t *f, uint32_t status_flags)
{
    if ((status_flags & 0xFu) == 0) return;
    for (int x = FRAME_COLS - 4; x < FRAME_COLS; x++) {
        frame_set_pixel(f, x, FRAME_ROWS - 1, false);
        frame_set_pixel(f, x, FRAME_ROWS - 2, false);
    }
    for (int i = 0; i < 4; i++) {
        if (status_flags & (1u << i)) frame_set_pixel(f, FRAME_COLS - 1 - i, FRAME_ROWS - 1, true);
    }
}

int frame_draw_text(frame_t *f, const char *text, int x_offset)
{
    int x = x_offset;
    int n = 0;
    for (const char *p = text; *p; p++, n++) {
        const glyph_t *g = find_glyph(*p);
        for (int r = 0; r < GLYPH_H; r++) {
            int y = TEXT_Y0 + (GLYPH_H - 1 - r);
            for (int c = 0; c < GLYPH_W; c++) {
                if (g->rows[r] & (1u << (GLYPH_W - 1 - c))) frame_set_pixel(f, x + c, y, true);
            }
        }
        x += GLYPH_W + GLYPH_GAP;
    }
    return n == 0 ? 0 : n * (GLYPH_W + GLYPH_GAP) - GLYPH_GAP;
}

/* ---------------- Mounting ---------------- */

/*
 * For every pixel (x, y): chip = x / 8, local column lx = x % 8, local row ly = y.
 * The orientation flags change those, then:
 *   not transposed: register (row) = ly, bit = 7 - lx  (bit 7 = left edge)
 *   transposed:     register (row) = lx, bit = ly
 * reverse_devices x flip_x x flip_y x transpose = 16 combinations, which covers
 * every way a chain of square modules can be mounted. Bring-up 01 cycles through them.
 */
void frame_to_device_rows(const frame_t *f, const frame_orient_t *orient,
                          int n_devices, uint8_t *out)
{
    memset(out, 0, (size_t)n_devices * 8);
    int cols = n_devices * 8 < FRAME_COLS ? n_devices * 8 : FRAME_COLS;
    for (int x = 0; x < cols; x++) {
        for (int y = 0; y < FRAME_ROWS; y++) {
            if (!frame_get_pixel(f, x, y)) continue;
            int dev = x / 8, lx = x % 8, ly = y;
            if (orient->reverse_devices) dev = n_devices - 1 - dev;
            if (orient->flip_x) lx = 7 - lx;
            if (orient->flip_y) ly = 7 - ly;
            int reg, bit;
            if (orient->transpose) { reg = lx; bit = ly; }
            else                   { reg = ly; bit = 7 - lx; }
            out[dev * 8 + reg] |= (uint8_t)(1u << bit);
        }
    }
}

void frame_print_ascii(const frame_t *f)
{
    for (int y = FRAME_ROWS - 1; y >= 0; y--) {
        for (int x = 0; x < FRAME_COLS; x++) putchar(frame_get_pixel(f, x, y) ? '#' : '.');
        putchar('\n');
    }
}
