/* Minimal register-level board support for the nRF52840-DK on FIT IoT-LAB (archi nrf52840dk:multi).
 * Same interface as soc/harness/stm32l4/board.h. CPU at 64 MHz from the external crystal (HFXO started so
 * the UART baud rate is exact); flash instruction cache left in its reset state (disabled); UART0 (legacy)
 * TX on P0.06, RX on P0.08 (the J-Link virtual COM port the testbed exposes on TCP 20000); DWT cycles. */
#include "board.h"

#define REG(a) (*(volatile uint32_t *)(a))
#define CLOCK_BASE 0x40000000u
#define CLOCK_TASKS_HFCLKSTART (CLOCK_BASE + 0x000u)
#define CLOCK_EVENTS_HFCLKSTARTED (CLOCK_BASE + 0x100u)
#define GPIO_P0 0x50000000u
#define GPIO_OUTSET (GPIO_P0 + 0x508u)
#define GPIO_PIN_CNF(n) (GPIO_P0 + 0x700u + 4u * (n))
#define UART0 0x40002000u
#define UART_TASKS_STARTTX (UART0 + 0x008u)
#define UART_EVENTS_TXDRDY (UART0 + 0x11Cu)
#define UART_ENABLE (UART0 + 0x500u)
#define UART_PSEL_TXD (UART0 + 0x50Cu)
#define UART_PSEL_RXD (UART0 + 0x514u)
#define UART_TXD (UART0 + 0x51Cu)
#define UART_BAUDRATE (UART0 + 0x524u)
#define UART_CONFIG (UART0 + 0x56Cu)
#define PIN_TX 6u
#define PIN_RX 8u

void board_init(void)
{
    REG(CLOCK_EVENTS_HFCLKSTARTED) = 0u;
    REG(CLOCK_TASKS_HFCLKSTART) = 1u;
    while (!REG(CLOCK_EVENTS_HFCLKSTARTED)) {
    }
    REG(GPIO_OUTSET) = (1u << PIN_TX);
    REG(GPIO_PIN_CNF(PIN_TX)) = 1u;       /* output */
    REG(GPIO_PIN_CNF(PIN_RX)) = 0u;       /* input, buffer connected */
    REG(UART_PSEL_TXD) = PIN_TX;
    REG(UART_PSEL_RXD) = PIN_RX;
    REG(UART_BAUDRATE) = 0x01D7E000u;     /* 115200 */
    REG(UART_CONFIG) = 0u;
    REG(UART_ENABLE) = 4u;
    REG(UART_TASKS_STARTTX) = 1u;
    /* DWT cycle counter */
    REG(0xE000EDFCu) |= (1u << 24);
    REG(0xE0001004u) = 0u;
    REG(0xE0001000u) |= 1u;
}

void uart_putc(char c)
{
    REG(UART_EVENTS_TXDRDY) = 0u;
    REG(UART_TXD) = (uint32_t)(uint8_t)c;
    while (!REG(UART_EVENTS_TXDRDY)) {
    }
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
