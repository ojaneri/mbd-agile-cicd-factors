/* E5 main: five passes over the embedded requirement vectors.
 *   pass 0: no paint (whatever the platform left in RAM: reset/power history, earlier calls)
 *   pass 1..4: the unused stack below the current SP is painted with 0x00000000, 0xFFFFFFFF,
 *              0xAAAAAAAA, 0x55555555 before the pass.
 * The subject's state lives in a noinline callee frame (e5_<subject>.c), i.e. inside the painted region. */
#include <stdint.h>
#include "board.h"
#include "e5_common.h"

extern uint32_t _ebss;
static const uint32_t E5_PAT[5] = {0u, 0x00000000u, 0xFFFFFFFFu, 0xAAAAAAAAu, 0x55555555u};

/* Naked: no frame of its own, so it paints every word from _ebss up to the caller's SP (main's), which
 * is exactly where e5_run_all and the subject's run_vector frames will live. No interrupts are enabled. */
__attribute__((naked, noinline)) static void e5_paint(uint32_t p)
{
    (void)p;
    __asm volatile(
        "ldr r1, =_ebss\n\t"
        "mov r2, sp\n\t"
        "1: cmp r1, r2\n\t"
        "bhs 2f\n\t"
        "str r0, [r1], #4\n\t"
        "b 1b\n\t"
        "2: bx lr\n\t"
        ".ltorg\n\t");
}

int main(void)
{
    board_init();
    e5_systick_start();
    uart_puts("\r\n@BEGIN\n");
#ifndef E5_PASSES
#define E5_PASSES 5u /* 1 for control and timing-ladder mutants (pass 0 only) */
#endif
    for (uint32_t k = 0; k < E5_PASSES; k++) {
        if (k > 0u) {
            e5_paint(E5_PAT[k]);
        }
        uart_puts("@P ");
        uart_putdec(k);
        uart_putc(' ');
        uart_puthex32(E5_PAT[k]);
        uart_putc('\n');
        e5_run_all();
    }
    uart_puts("@END\n");
    for (;;) {
    }
}
