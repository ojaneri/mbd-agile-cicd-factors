/* Test harness shared by SIL (host) and PIL-dev (QEMU, semihosting).
 * Input file:  first line "n", then n lines "dt maf rpm thr stft ltft".
 * Output file: n lines "rate vol" after each row. On PIL builds (PIL_TIMING) the last line is
 * "#ticks max total" for fuel_step.
 */
#include <stdio.h>
#include "fuel.h"

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
    fuel_t f;
    fuel_init(&f);
    double dt, maf, rpm, thr, st, lt;
#ifdef PIL_TIMING
    uint32_t tmax = 0u;
    uint64_t ttot = 0u;
    pil_timer_start();
#endif
    for (long j = 0; j < n; j++) {
        if (fscanf(fi, "%lf %lf %lf %lf %lf %lf", &dt, &maf, &rpm, &thr, &st, &lt) != 6) {
            return 5;
        }
#ifdef PIL_TIMING
        uint32_t t0 = pil_timer_now();
        fuel_step(&f, (float)dt, (float)maf, (float)rpm, (float)thr, (float)st, (float)lt);
        uint32_t dtk = pil_timer_elapsed(t0);
        if (dtk > tmax) {
            tmax = dtk;
        }
        ttot += dtk;
#else
        fuel_step(&f, (float)dt, (float)maf, (float)rpm, (float)thr, (float)st, (float)lt);
#endif
        fprintf(fo, "%.9g %.9g\n", (double)f.rate, (double)f.vol);
    }
#ifdef PIL_TIMING
    fprintf(fo, "#ticks %lu %llu\n", (unsigned long)tmax, (unsigned long long)ttot);
#endif
    fclose(fo);
    fclose(fi);
    return 0;
}
