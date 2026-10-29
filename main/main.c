/**
 * @file main.c
 * @brief Start-up order only — the work happens in the tasks.
 *
 * Spectrum Visualiser — Mini-Challenge 2 (CDIO)
 * Author: Joe Gould, with Claude (Anthropic) writing the implementation
 * Sources and credits: see README.md
 *
 * Planned start-up order:
 *   1. settings_init(), settings_load()
 *   2. create the 1-slot audio_frame_t queue
 *   3. display_task_start()  — so the display shows something early
 *   4. audio_task_start()    — with the saved mode
 *   5. input_task_start()
 *
 * STATUS: skeleton only.
 */
#include "app_config.h"
#include "app_types.h"

void app_main(void)
{
    /* TODO: start-up steps above */
}
