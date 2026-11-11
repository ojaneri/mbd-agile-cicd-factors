/* Test harness shared by SIL (host) and PIL-dev (QEMU, semihosting) for subject 3.
 * Input file:  first line "n", then n lines "rst cur tref" (rst = 1: bess_init(tref) before the step).
 * Output file: n lines "t_est der" after each row. On PIL builds (PIL_TIMING) the last line is
 * "#ticks max total" for bess_step.
 */
#include <stdio.h>
#include "bess.h"

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
    if (fscanf(fi, "%ld", &n) != 1) {
        return 4;
    }
    bess_t o;
    double rst, cur, tref;
#ifdef PIL_TIMING
    uint32_t tmax = 0u;
    uint64_t ttot = 0u;
    pil_timer_start();
#endif
    for (long j = 0; j < n; j++) {
        if (fscanf(fi, "%lf %lf %lf", &rst, &cur, &tref) != 3) {
            return 5;
        }
        if (rst > 0.5 || j == 0) {
            bess_init(&o, (float)tref);
        }
#ifdef PIL_TIMING
        uint32_t t0 = pil_timer_now();
        bess_step(&o, (float)cur, (float)tref);
        uint32_t dtk = pil_timer_elapsed(t0);
        if (dtk > tmax) {
            tmax = dtk;
        }
        ttot += dtk;
#else
        bess_step(&o, (float)cur, (float)tref);
#endif
        fprintf(fo, "%.9g %.9g\n", (double)o.t_est, (double)o.der);
    }
#ifdef PIL_TIMING
    fprintf(fo, "#ticks %lu %llu\n", (unsigned long)tmax, (unsigned long long)ttot);
#endif
    fclose(fo);
    fclose(fi);
    return 0;
}
