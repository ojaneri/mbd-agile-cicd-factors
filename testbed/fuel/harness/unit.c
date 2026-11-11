/* Unit tests of the generated C against the spec (expectations in fuel_expect.h).
 * Exit code 0 = all pass; prints one line per failed check. */
#include <math.h>
#include <stdio.h>
#include "fuel.h"
#include "fuel_expect.h"

static int fails = 0;

static void check(int ok, const char *what, int i, double got, double exp)
{
    if (!ok) {
        printf("FAIL %s[%d] got=%.9g exp=%.9g\n", what, i, got, exp);
        fails++;
    }
}

int main(void)
{
    /* U1: rate function (trim clamp, DFCO, saturation) equals the spec. */
    for (int i = 0; i < UT_N_RATE; i++) {
        const double *q = UT_RATE_IN[i];
        double r = (double)fuel_rate_of((float)q[0], (float)q[1], (float)q[2], (float)q[3], (float)q[4]);
        double e = UT_RATE_EXP[i];
        check(fabs(r - e) <= 1e-4 + 1e-5 * fabs(e), "U1 rate", i, r, e);
    }
    /* U2: one integration step from 100 ml, incl. dt clamping (dt > dt_max, dt < 0). */
    for (int i = 0; i < UT_N_STEP; i++) {
        const double *q = UT_STEP[i];
        fuel_t f;
        fuel_init(&f);
        f.vol = 100.0f;
        double v = (double)fuel_step(&f, (float)q[0], (float)q[1], (float)q[2], (float)q[3], (float)q[4], (float)q[5]);
        check(fabs(v - q[6]) <= 1e-3 + 1e-5 * fabs(q[6]), "U2 step", i, v, q[6]);
    }
    /* U3: init gives zero volume and rate. */
    fuel_t f;
    f.vol = 5.0f;
    f.rate = 5.0f;
    fuel_init(&f);
    check(f.vol == 0.0f && f.rate == 0.0f, "U3 init", 0, f.vol, 0.0);
    printf("unit fails=%d\n", fails);
    return fails ? 1 : 0;
}
