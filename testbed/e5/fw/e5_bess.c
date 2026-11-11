/* E5 adapter for subject 3 (BESS thermal sensor with derating): same call sequence as its E1 PIL main
 * (init at row 0 and on every reset row, step every row), state local to a noinline function.
 * Two words per row (t_est, der). */
#include "e5_common.h"
#include "bess.h"
#include "vectors.h"

__attribute__((noinline)) static void run_vector(uint32_t t)
{
    const pil_vector_t *v = &PIL_VECTORS[t];
    bess_t o;
    e5_vec_t s;
    e5_vec_begin(&s, t, v->n);
    for (uint32_t j = 0; j < v->n; j++) {
        if (v->rst[j] > 0.5f || j == 0u) {
            bess_init(&o, v->tref[j]);
        }
        e5_t0(&s);
        bess_step(&o, v->cur[j], v->tref[j]);
        e5_t1(&s);
        float w[2] = {o.t_est, o.der};
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
