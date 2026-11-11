#include "board.h"

#define REG(a) (*(volatile uint32_t *)(a))
#define RCC 0x40021000u
#define RCC_CR (RCC + 0x00u)
#define RCC_CFGR (RCC + 0x08u)
#define RCC_AHB2ENR (RCC + 0x4Cu)
#define RCC_APB1ENR1 (RCC + 0x58u)
#define RCC_APB2ENR (RCC + 0x60u)
#define GPIOA 0x48000000u
#define GPIOB 0x48000400u

#if defined(BOARD_NUCLEO_L476)
#define UART_BASE 0x40004400u /* USART2 */
#elif defined(BOARD_IOTNODE)
#define UART_BASE 0x40013800u /* USART1 */
#else
#error "define BOARD_NUCLEO_L476 or BOARD_IOTNODE"
#endif
#define UART_CR1 (UART_BASE + 0x00u)
#define UART_BRR (UART_BASE + 0x0Cu)
#define UART_ISR (UART_BASE + 0x1Cu)
#define UART_TDR (UART_BASE + 0x28u)

static void gpio_af7(uint32_t port, uint32_t pin)
{
    REG(port + 0x00u) = (REG(port + 0x00u) & ~(3u << (2u * pin))) | (2u << (2u * pin));   /* MODER = AF */
    uint32_t afr = port + (pin < 8u ? 0x20u : 0x24u);
    uint32_t sh = 4u * (pin & 7u);
    REG(afr) = (REG(afr) & ~(0xFu << sh)) | (7u << sh);                                     /* AF7 */
}

void board_init(void)
{
    /* HSI16 as SYSCLK; flash latency stays 0 WS (valid at 16 MHz, range 1). */
    REG(RCC_CR) |= (1u << 8);
    while (!(REG(RCC_CR) & (1u << 10))) {
    }
    REG(RCC_CFGR) = (REG(RCC_CFGR) & ~3u) | 1u;
    while (((REG(RCC_CFGR) >> 2) & 3u) != 1u) {
    }
#if defined(BOARD_NUCLEO_L476)
    REG(RCC_AHB2ENR) |= (1u << 0);
    REG(RCC_APB1ENR1) |= (1u << 17);
    gpio_af7(GPIOA, 2u);
    gpio_af7(GPIOA, 3u);
#else
    REG(RCC_AHB2ENR) |= (1u << 1);
    REG(RCC_APB2ENR) |= (1u << 14);
    gpio_af7(GPIOB, 6u);
    gpio_af7(GPIOB, 7u);
#endif
    REG(UART_CR1) = 0u;
    REG(UART_BRR) = (16000000u + PIL_BAUD / 2u) / PIL_BAUD;
    REG(UART_CR1) = (1u << 3) | (1u << 0); /* TE, UE */
    /* DWT cycle counter */
    REG(0xE000EDFCu) |= (1u << 24);
    REG(0xE0001004u) = 0u;
    REG(0xE0001000u) |= 1u;
}

void uart_putc(char c)
{
    while (!(REG(UART_ISR) & (1u << 7))) {
    }
    REG(UART_TDR) = (uint32_t)(uint8_t)c;
}

void uart_puts(const char *s)
{
    while (*s) {
        uart_putc(*s++);
    }
}

void uart_puthex32(uint32_t v)
{
    static const char hx[] = "0123456789abcdef";
    for (int i = 7; i >= 0; i--) {
        uart_putc(hx[(v >> (4 * i)) & 0xFu]);
    }
}

void uart_putdec(uint32_t v)
{
    char b[11];
    int i = 10;
    b[i] = 0;
    do {
        b[--i] = (char)('0' + v % 10u);
        v /= 10u;
    } while (v && i > 0);
    uart_puts(&b[i]);
}
