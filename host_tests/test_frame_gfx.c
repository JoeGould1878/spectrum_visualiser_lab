/**
 * @file test_frame_gfx.c
 * Laptop tests for frame_gfx: pixels, bars, peaks, text, and the
 * orientation mapping used by bring-up 01.
 */
#include <string.h>
#include "frame_gfx.h"
#include "test_util.h"

static int count_pixels(const frame_t *f)
{
    int n = 0;
    for (int x = 0; x < FRAME_COLS; x++)
        for (int y = 0; y < FRAME_ROWS; y++) n += frame_get_pixel(f, x, y);
    return n;
}

/* Which (byte index, bit) did a single pixel land in? Returns 1 if exactly one bit is set. */
static int find_bit(const uint8_t *rows, int n_bytes, int *idx, int *bit)
{
    int found = 0;
    for (int i = 0; i < n_bytes; i++)
        for (int b = 0; b < 8; b++)
            if (rows[i] & (1u << b)) { *idx = i; *bit = b; found++; }
    return found == 1;
}

static void map_one(int x, int y, frame_orient_t o, int *idx, int *bit)
{
    frame_t f;
    uint8_t rows[32];
    frame_clear(&f);
    frame_set_pixel(&f, x, y, true);
    frame_to_device_rows(&f, &o, 4, rows);
    CHECK(find_bit(rows, 32, idx, bit));
}

int main(void)
{
    frame_t f;

    /* set/get round trip; out-of-range ignored */
    frame_clear(&f);
    frame_set_pixel(&f, 5, 3, true);
    CHECK(frame_get_pixel(&f, 5, 3));
    CHECK(!frame_get_pixel(&f, 5, 2));
    frame_set_pixel(&f, -1, 0, true);
    frame_set_pixel(&f, 32, 0, true);
    frame_set_pixel(&f, 0, 8, true);
    CHECK(count_pixels(&f) == 1);
    CHECK(!frame_get_pixel(&f, 40, 40));
    frame_set_pixel(&f, 5, 3, false);
    CHECK(count_pixels(&f) == 0);

    /* bars: height h lights rows 0..h-1; clamps */
    for (int h = 0; h <= 8; h++) {
        frame_clear(&f);
        frame_draw_bar(&f, 7, h);
        CHECK(count_pixels(&f) == h);
        if (h > 0) CHECK(frame_get_pixel(&f, 7, h - 1));
    }
    frame_clear(&f);
    frame_draw_bar(&f, 0, 99);
    CHECK(f.col[0] == 0xFF);
    frame_draw_bar(&f, -3, 4);
    CHECK(count_pixels(&f) == 8);

    /* peak dot */
    frame_clear(&f);
    frame_draw_peak(&f, 2, 0);
    CHECK(count_pixels(&f) == 0);
    frame_draw_peak(&f, 2, 8);
    CHECK(frame_get_pixel(&f, 2, 7));

    /* text */
    frame_clear(&f);
    int w = frame_draw_text(&f, "440", 0);
    CHECK(w == 11);
    CHECK(frame_draw_text(&f, "", 0) == 0);
    CHECK(count_pixels(&f) > 0);
    frame_print_ascii(&f);
    frame_clear(&f);
    frame_draw_text(&f, "8", -100);   /* fully off-screen: no crash, nothing drawn */
    CHECK(count_pixels(&f) == 0);

    /* status: flags in the top-right, area cleared under them, bars untouched otherwise */
    frame_clear(&f);
    frame_draw_status(&f, FRAME_STATUS_SILENT | FRAME_STATUS_NOT_LISTENING);
    CHECK(frame_get_pixel(&f, 31, 7) && frame_get_pixel(&f, 28, 7));
    CHECK(count_pixels(&f) == 2);
    frame_clear(&f);
    for (int x = 0; x < 32; x++) frame_draw_bar(&f, x, 8);
    frame_draw_status(&f, 0);
    CHECK(count_pixels(&f) == 256);                 /* no flags: nothing changes */
    frame_draw_status(&f, FRAME_STATUS_CLIPPING);
    CHECK(frame_get_pixel(&f, 30, 7));              /* the flag */
    CHECK(!frame_get_pixel(&f, 31, 7) && !frame_get_pixel(&f, 30, 6));   /* cleared area */
    CHECK(frame_get_pixel(&f, 27, 7));              /* column 27 untouched */
    CHECK(count_pixels(&f) == 256 - 8 + 1);

    /* orientation mapping */
    int idx, bit;
    frame_orient_t none = {0};
    map_one(0, 0, none, &idx, &bit);          /* chip 0, row reg 0, left bit */
    CHECK(idx == 0 && bit == 7);
    map_one(9, 2, none, &idx, &bit);          /* chip 1, local x 1, row 2 */
    CHECK(idx == 8 + 2 && bit == 6);

    frame_orient_t rev = {.reverse_devices = true};
    map_one(0, 0, rev, &idx, &bit);
    CHECK(idx == 3 * 8 + 0 && bit == 7);

    frame_orient_t fx = {.flip_x = true};
    map_one(0, 0, fx, &idx, &bit);
    CHECK(idx == 0 && bit == 0);

    frame_orient_t fy = {.flip_y = true};
    map_one(0, 0, fy, &idx, &bit);
    CHECK(idx == 7 && bit == 7);

    frame_orient_t tr = {.transpose = true};
    map_one(3, 5, tr, &idx, &bit);            /* reg = lx, bit = ly */
    CHECK(idx == 3 && bit == 5);

    /* every orientation is a 1:1 mapping: a full frame lights all 256 bits */
    for (int k = 0; k < 16; k++) {
        frame_orient_t o = {k & 1, (k >> 1) & 1, (k >> 2) & 1, (k >> 3) & 1};
        uint8_t rows[32];
        memset(&f, 0xFF, sizeof(f));
        frame_to_device_rows(&f, &o, 4, rows);
        int ok = 1;
        for (int i = 0; i < 32; i++) ok &= rows[i] == 0xFF;
        CHECK(ok);
    }

    return TEST_RESULT();
}
