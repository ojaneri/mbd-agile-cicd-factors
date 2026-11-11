/* Unit tests of the generated C against the spec (expectations in bess_expect.h).
 * Exit code 0 = all pass; prints one line per failed check. */
#include <math.h>
#include <stdio.h>
#include "bess.h"
#include "bess_expect.h"

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
    /* U1: one thermal row (current clamp, sub-steps, temperature clamp). */
    for (int i = 0; i < UT_N_TH; i++) {
        const double *q = UT_TH[i];
        double t = (double)bess_therm((float)q[0], (float)q[1], (float)q[2]);
        check(fabs(t - q[3]) <= 1e-4 + 1e-6 * fabs(q[3]), "U1 therm", i, t, q[3]);
    }
    /* U2: one derating step from a given state (filter, latch, dwell, ramp). */
    for (int i = 0; i < UT_N_DR; i++) {
        const double *q = UT_DR[i];
        bess_t o;
        o.t_est = (float)q[4];
        o.t_filt = (float)q[0];
        o.latch = (int)q[1];
        o.dwell_ms = (uint32_t)q[2];
        o.der = (float)q[3];
        bess_derate(&o, (float)q[4]);
        check(fabs((double)o.t_filt - q[5]) <= 1e-4, "U2 t_filt", i, o.t_filt, q[5]);
        check((o.latch != 0) == (q[6] != 0.0), "U2 latch", i, o.latch, q[6]);
        check(fabs((double)o.dwell_ms - q[7]) < 0.5, "U2 dwell_ms", i, o.dwell_ms, q[7]);
        check(fabs((double)o.der - q[8]) <= 1e-5, "U2 der", i, o.der, q[8]);
    }
    /* U3: init from garbage gives the specified state. */
    bess_t o;
    o.t_est = 5.0f;
    o.t_filt = 5.0f;
    o.der = 5.0f;
    o.latch = 5;
    o.dwell_ms = 5u;
    bess_init(&o, 25.0f);
    check(fabs((double)o.t_est - UT_INIT_T) <= 1e-4, "U3 init t_est", 0, o.t_est, UT_INIT_T);
    check(fabs((double)o.t_filt - UT_INIT_T) <= 1e-4, "U3 init t_filt", 0, o.t_filt, UT_INIT_T);
    check(o.der == 1.0f, "U3 init der", 0, o.der, 1.0);
    check(o.latch == 0, "U3 init latch", 0, o.latch, 0.0);
    check(o.dwell_ms == 0u, "U3 init dwell", 0, o.dwell_ms, 0.0);
    printf("unit fails=%d\n", fails);
    return fails ? 1 : 0;
}
