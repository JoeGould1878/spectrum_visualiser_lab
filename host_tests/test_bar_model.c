/**
 * @file test_bar_model.c
 * Laptop tests for bar_model: scaling, fast rise / slow fall, peak hold.
 */
#include "bar_model.h"
#include "test_util.h"

int main(void)
{
    bar_model_cfg_t cfg = {
        .rows = 8, .floor_db = -60.0f, .db_per_row = 4.0f,
        .fall_rows_per_s = 20.0f, .peak_hold_s = 0.5f, .peak_fall_rows_per_s = 6.0f,
    };
    bar_model_t m;
    float db[2];

    /* scaling */
    bar_model_init(&m, &cfg, 2);
    db[0] = -60.0f; db[1] = -60.0f + 8 * 4.0f;
    bar_model_update(&m, db, 0.025f);
    CHECK(bar_model_height(&m, 0) == 0);
    CHECK(bar_model_height(&m, 1) == 8);
    db[1] = 0.0f;                                   /* much louder: clamped */
    bar_model_update(&m, db, 0.025f);
    CHECK(bar_model_height(&m, 1) == 8);
    db[0] = -60.0f + 3.9f;                          /* just under one row: not lit */
    bar_model_update(&m, db, 0.025f);
    CHECK(bar_model_height(&m, 0) == 0);
    db[0] = -60.0f + 4 * 4.0f;
    bar_model_update(&m, db, 0.025f);
    CHECK(bar_model_height(&m, 0) == 4);
    CHECK(bar_model_height(&m, 5) == 0);            /* out of range column */

    /* fast rise: one loud frame -> full height at once */
    bar_model_init(&m, &cfg, 1);
    db[0] = -20.0f;
    bar_model_update(&m, db, 0.025f);
    CHECK(bar_model_height(&m, 0) == 8);

    /* slow fall: 20 rows/s * 0.1 s = 2 rows per update */
    db[0] = -100.0f;
    bar_model_update(&m, db, 0.1f);
    CHECK_NEAR(m.level[0], 6.0, 1e-4);
    bar_model_update(&m, db, 0.1f);
    CHECK_NEAR(m.level[0], 4.0, 1e-4);
    for (int i = 0; i < 10; i++) bar_model_update(&m, db, 0.1f);
    CHECK(bar_model_height(&m, 0) == 0);           /* never below 0 */

    /* peak: holds 0.5 s at 8, then falls at 6 rows/s, never below the bar */
    bar_model_init(&m, &cfg, 1);
    db[0] = -20.0f;
    bar_model_update(&m, db, 0.025f);
    CHECK(bar_model_peak_row(&m, 0) == 8);
    db[0] = -100.0f;
    for (int i = 0; i < 4; i++) bar_model_update(&m, db, 0.1f);   /* 0.4 s: still held */
    CHECK(bar_model_peak_row(&m, 0) == 8);
    bar_model_update(&m, db, 0.1f);                 /* 0.5 s: hold not yet exceeded */
    bar_model_update(&m, db, 0.1f);                 /* 0.6 s: falls 0.6 rows */
    CHECK_NEAR(m.peak[0], 7.4, 1e-4);
    for (int i = 0; i < 30; i++) bar_model_update(&m, db, 0.1f);
    CHECK(bar_model_peak_row(&m, 0) == 0);

    return TEST_RESULT();
}
