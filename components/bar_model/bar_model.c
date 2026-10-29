/**
 * @file bar_model.c
 * @brief dB -> bar height with fast-rise / slow-fall and peak dots (pure C).
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 * Credits / sources used: none adapted (standard VU-meter ballistics).
 */
#include <string.h>
#include "bar_model.h"

void bar_model_init(bar_model_t *m, const bar_model_cfg_t *cfg, int cols)
{
    memset(m, 0, sizeof(*m));
    m->cfg = *cfg;
    m->cols = cols > BAR_MODEL_MAX_COLS ? BAR_MODEL_MAX_COLS : cols;
}

void bar_model_update(bar_model_t *m, const float *col_db, float dt_s)
{
    const bar_model_cfg_t *k = &m->cfg;
    for (int c = 0; c < m->cols; c++) {
        float target = (col_db[c] - k->floor_db) / k->db_per_row;
        if (target < 0.0f) target = 0.0f;
        if (target > (float)k->rows) target = (float)k->rows;

        /* fast rise, slow fall */
        if (target >= m->level[c]) {
            m->level[c] = target;
        } else {
            float fallen = m->level[c] - k->fall_rows_per_s * dt_s;
            m->level[c] = fallen > target ? fallen : target;
        }

        /* peak dot: hold, then fall, never below the bar */
        if (m->level[c] >= m->peak[c]) {
            m->peak[c] = m->level[c];
            m->peak_age_s[c] = 0.0f;
        } else {
            m->peak_age_s[c] += dt_s;
            if (m->peak_age_s[c] > k->peak_hold_s) {
                float fallen = m->peak[c] - k->peak_fall_rows_per_s * dt_s;
                m->peak[c] = fallen > m->level[c] ? fallen : m->level[c];
            }
        }
    }
}

/*
 * Truncate, not round: a row lights only once the level has fully reached it,
 * so noise just above the floor doesn't light a pixel (quiet-room test, R5).
 */
int bar_model_height(const bar_model_t *m, int col)
{
    if (col < 0 || col >= m->cols) return 0;
    return (int)m->level[col];
}

int bar_model_peak_row(const bar_model_t *m, int col)
{
    if (col < 0 || col >= m->cols) return 0;
    return (int)m->peak[col];
}
