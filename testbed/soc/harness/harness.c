/* Test harness shared by SIL (host) and PIL-dev (QEMU, semihosting).
 * Input file:  first line "n soc_override", then n lines "I V".
 * Output file: n lines with the SoC estimate after each row (row 0 = after init).
 * On PIL builds (PIL_TIMING defined) it also writes "#ticks max total" as the last line.
 */
#include <stdio.h>
#include <stdlib.h>
#include "soc_obs.h"

#ifdef PIL_TIMING
#include "pil_timer.h"
#endif

int main(int argc, char **argv)
{
    if (argc < 3) {
        return 2;
    }
    FILE *fi = fopen(argv[1], "r");
    FILE *fo = fopen(argv[2], "w");
    if (!fi || !fo) {
        return 3;
    }
    long n;
    double ov;
    if (fscanf(fi, "%ld %lf", &n, &ov) != 2) {
        return 4;
    }
    soc_obs_t o;
    double i_meas, v_meas;
#ifdef PIL_TIMING
    uint32_t tmax = 0u;
    uint64_t ttot = 0u;
    pil_timer_start();
#endif
    for (long j = 0; j < n; j++) {
        if (fscanf(fi, "%lf %lf", &i_meas, &v_meas) != 2) {
            return 5;
        }
        float s;
        if (j == 0) {
            soc_obs_init(&o, (float)v_meas, (float)ov);
            s = o.soc;
        } else {
#ifdef PIL_TIMING
            uint32_t t0 = pil_timer_now();
            s = soc_obs_step(&o, (float)i_meas, (float)v_meas);
            uint32_t dtk = pil_timer_elapsed(t0);
            if (dtk > tmax) {
                tmax = dtk;
            }
            ttot += dtk;
#else
            s = soc_obs_step(&o, (float)i_meas, (float)v_meas);
#endif
        }
        fprintf(fo, "%.9g\n", (double)s);
    }
#ifdef PIL_TIMING
    fprintf(fo, "#ticks %lu %llu\n", (unsigned long)tmax, (unsigned long long)ttot);
#endif
    fclose(fo);
    fclose(fi);
    return 0;
}
