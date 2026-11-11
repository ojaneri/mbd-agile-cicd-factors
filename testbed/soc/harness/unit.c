/* Unit tests of the generated C against the spec (expectations in soc_obs_expect.h).
 * Exit code 0 = all pass; prints one line per failed check. */
#include <math.h>
#include <stdio.h>
#include "soc_obs.h"
#include "soc_obs_expect.h"

static int fails = 0;

static void check(int ok, const char *what, double got, double exp)
{
    if (!ok) {
        printf("FAIL %s got=%.9g exp=%.9g\n", what, got, exp);
        fails++;
    }
}

int main(void)
{
    /* U1: OCV lookup equals the spec's piecewise-linear table, inside and outside [0,1]. */
    for (int i = 0; i < UT_N_OCV; i++) {
        double v = (double)soc_obs_ocv((float)UT_OCV_S[i]);
        check(fabs(v - UT_OCV_V[i]) <= 1e-4, "U1 ocv", v, UT_OCV_V[i]);
    }
    /* U2: inverse lookup round-trips inside (0,1). */
    for (int i = 0; i < UT_N_INV; i++) {
        float v = soc_obs_ocv((float)UT_INV_S[i]);
        double s = (double)soc_obs_ocv_inv(v);
        check(fabs(s - UT_INV_S[i]) <= 1e-3, "U2 ocv_inv", s, UT_INV_S[i]);
    }
    /* U3: at rest with V = OCV(s), the estimate stays at s (no drift) over 100 steps. */
    for (int i = 2; i < UT_N_INV - 2; i += 4) {
        soc_obs_t o;
        float v = soc_obs_ocv((float)UT_INV_S[i]);
        soc_obs_init(&o, v, (float)UT_INV_S[i]);
        float s = o.soc;
        for (int j = 0; j < 100; j++) {
            s = soc_obs_step(&o, 0.0f, v);
        }
        check(fabs((double)s - UT_INV_S[i]) <= 2e-3, "U3 rest_hold", s, UT_INV_S[i]);
    }
    /* U4: saturation keeps the estimate in [0,1] under strong charge/discharge (if the spec has it). */
    if (UT_SAT) {
        soc_obs_t o;
        soc_obs_init(&o, 4.2f, 1.0f);
        float s = 0.0f;
        for (int j = 0; j < 50; j++) {
            s = soc_obs_step(&o, 10.0f, 4.4f);
        }
        check(s <= 1.0f && s >= 0.0f, "U4 sat_high", s, 1.0);
        soc_obs_init(&o, 2.8f, 0.0f);
        for (int j = 0; j < 50; j++) {
            s = soc_obs_step(&o, -10.0f, 2.5f);
        }
        check(s <= 1.0f && s >= 0.0f, "U4 sat_low", s, 0.0);
    }
    printf("unit fails=%d\n", fails);
    return fails ? 1 : 0;
}
