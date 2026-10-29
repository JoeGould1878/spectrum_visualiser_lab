/**
 * @file main.c
 * @brief Bring-up 01 — MAX7219 matrix.
 *
 * Author: Joe Gould, with Claude (Anthropic) writing the implementation
 *
 * Steps (see bringup/README.md for wiring and what to record):
 *   1. max7219_init(), then test mode ON for 2 s -> every LED lit?
 *   2. Test mode off, intensity 1, clear.
 *   3. Light chip 0 row 0 only -> which chip, which edge? (photo)
 *   4. Draw an arrow with frame_gfx pointing to column 0 / row 0, convert with
 *      frame_to_device_rows(), write -> adjust frame_orient_t until correct.
 *   5. Bars of height 1..8 across all 32 columns (staircase) -> photo.
 *   6. Leave the staircase running 5 min -> any random pixels? (3.3 V logic)
 *
 * STATUS: skeleton only.
 */

void app_main(void)
{
    /* TODO: steps 1-6 */
}
