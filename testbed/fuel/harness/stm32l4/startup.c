/* Startup for STM32L47x: copy .data, zero .bss, enable the FPU, call main. No interrupts used. */
#include <stdint.h>

extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss, _estack;
int main(void);

void Reset_Handler(void)
{
    uint32_t *src = &_sidata;
    for (uint32_t *dst = &_sdata; dst < &_edata;) {
        *dst++ = *src++;
    }
    for (uint32_t *dst = &_sbss; dst < &_ebss;) {
        *dst++ = 0u;
    }
    *(volatile uint32_t *)0xE000ED88u |= (0xFu << 20); /* CP10/CP11 full access */
    __asm volatile("dsb\n isb");
    (void)main();
    for (;;) {
    }
}

void Default_Handler(void)
{
    for (;;) {
    }
}

__attribute__((section(".isr_vector"), used)) const void *const vectors[16] = {
    &_estack, (void *)Reset_Handler,
    (void *)Default_Handler, (void *)Default_Handler, (void *)Default_Handler,
    (void *)Default_Handler, (void *)Default_Handler, 0, 0, 0, 0,
    (void *)Default_Handler, (void *)Default_Handler, 0,
    (void *)Default_Handler, (void *)Default_Handler,
};
