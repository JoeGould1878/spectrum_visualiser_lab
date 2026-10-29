/**
 * @file test_frame_gfx.c
 * Tests to write:
 *  - set/get pixel round-trip; out-of-range coordinates are ignored, no crash
 *  - draw_bar heights 0..8 light exactly that many pixels
 *  - draw_text "440" returns a sensible width; print it with frame_print_ascii
 *  - to_device_rows with no flips: known pixel ends up in the expected byte/bit
 *  - each orientation flag moves that pixel where you expect
 */
#include "frame_gfx.h"
#include "test_util.h"

int main(void)
{
    /* TODO: tests above */
    return TEST_RESULT();
}
