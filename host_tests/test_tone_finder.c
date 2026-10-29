/**
 * @file test_tone_finder.c
 * Tests to write:
 *  - all bins at -100 dB -> valid == false
 *  - one peak exactly on bin 10 -> hz == 10 * bin_hz
 *  - peak between bins (synthetic, neighbours unequal) -> hz between the two bins
 *  - loud DC bin below min_bin is ignored
 *  - (later) synthesise a real sine, run a plain DFT, check 440 Hz within one bin
 */
#include "tone_finder.h"
#include "test_util.h"

int main(void)
{
    /* TODO: tests above */
    return TEST_RESULT();
}
