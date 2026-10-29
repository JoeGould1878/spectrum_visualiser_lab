/**
 * @file test_tone_finder.c
 * Laptop tests for tone_finder, including a synthetic sine through a
 * Hann window and a plain DFT (same processing as on the ESP32, minus esp-dsp).
 */
#include <math.h>
#include <stdio.h>
#include "tone_finder.h"
#include "test_util.h"

#define N     1024
#define FS    40000.0
#define PI    3.14159265358979323846

/* Hann-windowed sine -> dB magnitude spectrum, N/2 bins. */
static void synth_spectrum(double hz, float *db)
{
    static double x[N];
    for (int i = 0; i < N; i++) {
        double w = 0.5 - 0.5 * cos(2 * PI * i / (N - 1));
        x[i] = w * 1000.0 * sin(2 * PI * hz * i / FS);
    }
    for (int k = 0; k < N / 2; k++) {
        double re = 0, im = 0;
        for (int i = 0; i < N; i++) {
            re += x[i] * cos(2 * PI * k * i / N);
            im -= x[i] * sin(2 * PI * k * i / N);
        }
        db[k] = (float)(20 * log10(sqrt(re * re + im * im) + 1e-9));
    }
}

int main(void)
{
    float db[N / 2];
    const float bin = FS / N;

    /* silence -> invalid */
    for (int k = 0; k < N / 2; k++) db[k] = -100.0f;
    tone_t t = tone_find(db, N / 2, bin, 2, -50.0f);
    CHECK(!t.valid);

    /* symmetric peak exactly on bin 10 */
    db[9] = -20.0f; db[10] = -10.0f; db[11] = -20.0f;
    t = tone_find(db, N / 2, bin, 2, -50.0f);
    CHECK(t.valid && t.bin == 10);
    CHECK_NEAR(t.hz, 10 * bin, 1e-3);

    /* right neighbour louder -> estimate moves above bin 10, below bin 11 */
    db[11] = -13.0f;
    t = tone_find(db, N / 2, bin, 2, -50.0f);
    CHECK(t.hz > 10 * bin && t.hz < 11 * bin);

    /* loud DC below min_bin is ignored */
    db[0] = 0.0f;
    t = tone_find(db, N / 2, bin, 2, -50.0f);
    CHECK(t.bin == 10);

    /* real sines: error well under one bin (39 Hz) */
    const double tones[] = {150.0, 440.0, 1000.0, 1234.5, 3000.0, 7777.0};
    printf("  set Hz   found Hz   error Hz\n");
    for (size_t i = 0; i < sizeof(tones) / sizeof(tones[0]); i++) {
        synth_spectrum(tones[i], db);
        t = tone_find(db, N / 2, bin, 2, 0.0f);
        printf("  %7.1f  %8.1f  %+8.2f\n", tones[i], t.hz, t.hz - tones[i]);
        CHECK(t.valid);
        CHECK_NEAR(t.hz, tones[i], 0.25 * bin);
    }

    return TEST_RESULT();
}
