/* Real-target PIL run: all embedded vectors (requirement tests + field cycles), output streamed as
 * float32 bit patterns in hex, one line per row, with a per-vector CRC32 and DWT cycle statistics.
 *   @BEGIN
 *   @T <idx> <n>
 *   <8 hex digits>            (n lines)
 *   @S <idx> <crc32> <max_cycles> <total_cycles_lo32>
 *   @END
 */
#include <stdint.h>
#include <string.h>
#include "board.h"
#include "soc_obs.h"
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
        soc_obs_t o;
        uint32_t crc = 0xFFFFFFFFu, cmax = 0u, ctot = 0u;
        uart_puts("@T ");
        uart_putdec(t);
        uart_putc(' ');
        uart_putdec(v->n);
        uart_putc('\n');
        for (uint32_t j = 0; j < v->n; j++) {
            float s;
            if (j == 0u) {
                soc_obs_init(&o, v->V[0], v->override);
                s = o.soc;
            } else {
                uint32_t c0 = cycles_now();
                s = soc_obs_step(&o, v->I[j], v->V[j]);
                uint32_t dc = cycles_now() - c0;
                if (dc > cmax) {
                    cmax = dc;
                }
                ctot += dc;
            }
            uint32_t bits;
            memcpy(&bits, &s, sizeof bits);
            crc = crc32_update(crc, bits);
            uart_puthex32(bits);
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
