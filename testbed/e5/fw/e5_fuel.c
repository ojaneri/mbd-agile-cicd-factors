/* E5 adapter for subject 2 (fuel-flow sensor): same call sequence as the E1 PIL main (init once,
 * step every row), state local to a noinline function. Two words per row (rate, vol). */
#include "e5_common.h"
#include "fuel.h"
#include "vectors.h"

__attribute__((noinline)) static void run_vector(uint32_t t)
{
    const pil_vector_t *v = &PIL_VECTORS[t];
    fuel_t f;
    e5_vec_t s;
    fuel_init(&f);
    e5_vec_begin(&s, t, v->n);
    for (uint32_t j = 0; j < v->n; j++) {
        e5_t0(&s);
        fuel_step(&f, v->dt[j], v->maf[j], v->rpm[j], v->thr[j], v->stft[j], v->ltft[j]);
        e5_t1(&s);
        float w[2] = {f.rate, f.vol};
        e5_row(&s, w, 2);
    }
    e5_vec_end(&s);
}

void e5_run_all(void)
{
    for (uint32_t t = 0; t < PIL_N_VECTORS; t++) {
        run_vector(t);
    }
}
