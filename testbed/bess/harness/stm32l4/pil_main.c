/* Real-target PIL run for subject 3: the embedded requirement vectors (the field vector does not fit in
 * flash), output streamed as float32 bit patterns in hex, "t_est der" per row, with a per-vector CRC32 over
 * both words and DWT cycle statistics of bess_step.
 *   @BEGIN
 *   @T <idx> <n>
 *   <8 hex> <8 hex>           (n lines: t_est, der)
 *   @S <idx> <crc32> <max_cycles> <total_cycles_lo32>
 *   @END
 */
#include <stdint.h>
#include <string.h>
#include "board.h"
#include "bess.h"
#include "vectors.h"

static uint32_t crc32_update(uint32_t crc, uint32_t w)
{
    for (int b = 0; b < 4; b++) {
        crc ^= (w >> (8 * b)) & 0xFFu;
        for (int k = 0; k < 8; k++) {
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
        }
    }
    return crc;
}

int main(void)
{
    board_init();
    uart_puts("\r\n@BEGIN\n");
    for (uint32_t t = 0; t < PIL_N_VECTORS; t++) {
        const pil_vector_t *v = &PIL_VECTORS[t];
        bess_t o;
        uint32_t crc = 0xFFFFFFFFu, cmax = 0u, ctot = 0u;
        uart_puts("@T ");
        uart_putdec(t);
        uart_putc(' ');
        uart_putdec(v->n);
        uart_putc('\n');
        for (uint32_t j = 0; j < v->n; j++) {
            if (v->rst[j] > 0.5f || j == 0u) {
                bess_init(&o, v->tref[j]);
            }
            uint32_t c0 = cycles_now();
            bess_step(&o, v->cur[j], v->tref[j]);
            uint32_t dc = cycles_now() - c0;
            if (dc > cmax) {
                cmax = dc;
            }
            ctot += dc;
            uint32_t bt, bd;
            memcpy(&bt, &o.t_est, sizeof bt);
            memcpy(&bd, &o.der, sizeof bd);
            crc = crc32_update(crc, bt);
            crc = crc32_update(crc, bd);
            uart_puthex32(bt);
            uart_putc(' ');
            uart_puthex32(bd);
            uart_putc('\n');
        }
        uart_puts("@S ");
        uart_putdec(t);
        uart_putc(' ');
        uart_puthex32(~crc);
        uart_putc(' ');
        uart_putdec(cmax);
        uart_putc(' ');
        uart_putdec(ctot);
        uart_putc('\n');
    }
    uart_puts("@END\n");
    for (;;) {
    }
}
