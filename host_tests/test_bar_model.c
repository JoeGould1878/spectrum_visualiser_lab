/**
 * @file test_bar_model.c
 * Tests to write:
 *  - level at floor_db -> height 0; floor + 8 * db_per_row -> height 8; louder -> still 8
 *  - fast rise: one loud frame -> full height immediately
 *  - slow fall: after silence, height drops by fall_rows_per_s * dt each update
 *  - peak dot holds for peak_hold_s, then falls
 */
#include "bar_model.h"
#include "test_util.h"

int main(void)
{
    /* TODO: tests above */
    return TEST_RESULT();
}
