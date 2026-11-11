/* PIL-dev startup for QEMU mps2-an386 (Cortex-M4). Development only: QEMU has no timing model. */
#include <stdint.h>

extern void _start(void);           /* newlib rdimon crt0 (semihosting argv, bss, main) */
extern uint32_t __StackTop;

void Reset_Handler(void);
void Default_Handler(void);

void Reset_Handler(void)
{
    volatile uint32_t *cpacr = (volatile uint32_t *)0xE000ED88u;
    *cpacr |= (0xFu << 20);          /* enable CP10/CP11 (FPU) */
    __asm volatile("dsb\n isb");
    _start();
    for (;;) {
    }
}

void Default_Handler(void)
{
    for (;;) {
    }
}

__attribute__((section(".vectors"), used)) const void *const vectors[16] = {
    &__StackTop, (void *)Reset_Handler,
    (void *)Default_Handler, (void *)Default_Handler, (void *)Default_Handler,
    (void *)Default_Handler, (void *)Default_Handler, 0, 0, 0, 0,
    (void *)Default_Handler, (void *)Default_Handler, 0,
    (void *)Default_Handler, (void *)Default_Handler,
};
