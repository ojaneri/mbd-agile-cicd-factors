/* Real-target PIL run for subject 2: the embedded requirement vectors (field tanks do not fit in flash),
 * output streamed as float32 bit patterns in hex, "rate vol" per row, with a per-vector CRC32 over both
 * words and DWT cycle statistics of fuel_step.
 *   @BEGIN
 *   @T <idx> <n>
 *   <8 hex> <8 hex>           (n lines: rate, vol)
 *   @S <idx> <crc32> <max_cycles> <total_cycles_lo32>
 *   @END
 */
#include <stdint.h>
#include <string.h>
#include "board.h"
#include "fuel.h"
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
        fuel_t f;
        fuel_init(&f);
        uint32_t crc = 0xFFFFFFFFu, cmax = 0u, ctot = 0u;
        uart_puts("@T ");
        uart_putdec(t);
        uart_putc(' ');
        uart_putdec(v->n);
        uart_putc('\n');
        for (uint32_t j = 0; j < v->n; j++) {
            uint32_t c0 = cycles_now();
            fuel_step(&f, v->dt[j], v->maf[j], v->rpm[j], v->thr[j], v->stft[j], v->ltft[j]);
            uint32_t dc = cycles_now() - c0;
            if (dc > cmax) {
                cmax = dc;
            }
            ctot += dc;
            uint32_t br, bv;
            memcpy(&br, &f.rate, sizeof br);
            memcpy(&bv, &f.vol, sizeof bv);
            crc = crc32_update(crc, br);
            crc = crc32_update(crc, bv);
            uart_puthex32(br);
            uart_putc(' ');
            uart_puthex32(bv);
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
