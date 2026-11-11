/* E5 adapter for subject 1 (SoC observer): same call sequence as the E1 PIL main (init at row 0,
 * step from row 1), but the state is a local of a noinline function. One word per row (SoC). */
#include "e5_common.h"
#include "soc_obs.h"
#include "vectors.h"

__attribute__((noinline)) static void run_vector(uint32_t t)
{
    const pil_vector_t *v = &PIL_VECTORS[t];
    soc_obs_t o;
    e5_vec_t s;
    e5_vec_begin(&s, t, v->n);
    for (uint32_t j = 0; j < v->n; j++) {
        float x;
        if (j == 0u) {
            soc_obs_init(&o, v->V[0], v->override);
            x = o.soc;
        } else {
            e5_t0(&s);
            x = soc_obs_step(&o, v->I[j], v->V[j]);
            e5_t1(&s);
        }
        e5_row(&s, &x, 1);
    }
    e5_vec_end(&s);
}

void e5_run_all(void)
{
    for (uint32_t t = 0; t < PIL_N_VECTORS; t++) {
        run_vector(t);
    }
}
