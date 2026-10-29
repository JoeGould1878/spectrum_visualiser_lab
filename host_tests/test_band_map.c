/**
 * @file test_band_map.c
 * Tests to write (one at a time):
 *  - linear, 32 cols, 0-6 kHz, 187.5 Hz bins: one bin per column (Aidan's setup)
 *  - every column has first_bin <= last_bin, columns don't overlap, no gaps
 *  - hybrid log, 100 Hz - 8 kHz, 39 Hz bins: bottom columns one bin each,
 *    edges increase, last edge = 8 kHz
 *  - f_max above Nyquist -> build returns -1
 *  - band_map_apply: a single loud bin lands in the right column
 *  - band_map_column_for_hz: 440 Hz, 1 kHz, below f_min (-1), above f_max (-1)
 */
#include "band_map.h"
#include "test_util.h"

int main(void)
{
    /* TODO: tests above */
    return TEST_RESULT();
}
