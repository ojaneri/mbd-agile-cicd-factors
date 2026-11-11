/* E5 firmware helpers shared by all subjects. The SAME ELF runs on QEMU (b-l475e-iot01a) and on the
 * real STM32L475VG (FIT IoT-LAB st-iotnode), so any verdict difference is the platform, not the harness.
 * Stream:  @BEGIN / @P <pass> <pattern> / @T <idx> <n> / rows of K hex words / @S <idx> <crc32> <max_systick> <max_dwt> / @END
 * Timing: SysTick (24-bit, processor clock) on both platforms: core cycles on the board, an instruction
 * proxy under QEMU -icount. DWT CYCCNT is also reported (0 under QEMU, which does not model it). */
#ifndef E5_COMMON_H
#define E5_COMMON_H
#include <stdint.h>
#include <string.h>
#include "board.h"

#define E5_SYST_CSR (*(volatile uint32_t *)0xE000E010u)
#define E5_SYST_RVR (*(volatile uint32_t *)0xE000E014u)
#define E5_SYST_CVR (*(volatile uint32_t *)0xE000E018u)

static inline void e5_systick_start(void)
{
    E5_SYST_RVR = 0x00FFFFFFu;
    E5_SYST_CVR = 0u;
    E5_SYST_CSR = 5u; /* enable, processor clock, no interrupt */
}

typedef struct {
    uint32_t idx, crc, st0, dw0, st_max, dw_max;
} e5_vec_t;

static inline uint32_t e5_crc32_update(uint32_t crc, uint32_t w)
{
    for (int b = 0; b < 4; b++) {
        crc ^= (w >> (8 * b)) & 0xFFu;
        for (int k = 0; k < 8; k++) {
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
        }
    }
    return crc;
}

static inline void e5_vec_begin(e5_vec_t *s, uint32_t idx, uint32_t n)
{
    s->idx = idx;
    s->crc = 0xFFFFFFFFu;
    s->st_max = 0u;
    s->dw_max = 0u;
    uart_puts("@T ");
    uart_putdec(idx);
    uart_putc(' ');
    uart_putdec(n);
    uart_putc('\n');
}

static inline void e5_t0(e5_vec_t *s)
{
    s->dw0 = cycles_now();
    s->st0 = E5_SYST_CVR;
}

static inline void e5_t1(e5_vec_t *s)
{
    uint32_t st = (s->st0 - E5_SYST_CVR) & 0x00FFFFFFu;
    uint32_t dw = cycles_now() - s->dw0;
    if (st > s->st_max) {
        s->st_max = st;
    }
    if (dw > s->dw_max) {
        s->dw_max = dw;
    }
}

static inline void e5_row(e5_vec_t *s, const float *vals, int k)
{
    for (int i = 0; i < k; i++) {
        uint32_t bits;
        memcpy(&bits, &vals[i], sizeof bits);
        s->crc = e5_crc32_update(s->crc, bits);
        if (i) {
            uart_putc(' ');
        }
        uart_puthex32(bits);
    }
    uart_putc('\n');
}

static inline void e5_vec_end(e5_vec_t *s)
{
    uart_puts("@S ");
    uart_putdec(s->idx);
    uart_putc(' ');
    uart_puthex32(~s->crc);
    uart_putc(' ');
    uart_putdec(s->st_max);
    uart_putc(' ');
    uart_putdec(s->dw_max);
    uart_putc('\n');
}

void e5_run_all(void); /* subject file: runs every embedded vector once (state local to a callee frame) */
#endif
