/**
 * @file main.c
 * @brief Bring-up 02 — MAX9814 mic -> continuous ADC.
 *
 * Author: Joe Gould, with Claude (Anthropic) writing the implementation
 *
 * Steps (see bringup/README.md for wiring and what to record):
 *   1. adc_sampler_init() on GPIO 1 at the requested rate, start.
 *   2. Every second print:  RATE,<measured Hz>
 *   3. Every second print one frame as:  RAW,<n>,<v0>,...  (e.g. n = 1024)
 *   4. Record: quiet room, talking, clap, phone 1 kHz tone — at gain
 *      40 / 50 / 60 dB (MAX9814 Gain pin).
 *   5. Try a few requested rates; record requested vs measured.
 *
 * STATUS: skeleton only.
 */

void app_main(void)
{
    /* TODO: steps 1-3 */
}
