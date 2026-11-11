/* SysTick-based tick counter. Under QEMU with -icount the count is an instruction proxy, not time. */
#ifndef PIL_TIMER_H
#define PIL_TIMER_H
#include <stdint.h>

#define SYST_CSR (*(volatile uint32_t *)0xE000E010u)
#define SYST_RVR (*(volatile uint32_t *)0xE000E014u)
#define SYST_CVR (*(volatile uint32_t *)0xE000E018u)

static inline void pil_timer_start(void)
{
    SYST_RVR = 0x00FFFFFFu;
    SYST_CVR = 0u;
    SYST_CSR = 5u; /* enable, processor clock, no interrupt */
}

static inline uint32_t pil_timer_now(void)
{
    return SYST_CVR;
}

static inline uint32_t pil_timer_elapsed(uint32_t t0)
{
    return (t0 - SYST_CVR) & 0x00FFFFFFu; /* down-counter */
}
#endif
