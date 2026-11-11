/* Minimal register-level board support for STM32L476RG (NUCLEO) and STM32L475VG (B-L475E-IOT01A,
 * FIT IoT-LAB st-iotnode). SYSCLK = HSI16 (16 MHz, 0 flash wait states), UART at PIL_BAUD, DWT cycles.
 * Select the board with -DBOARD_NUCLEO_L476 (USART2 PA2/PA3, ST-LINK VCP) or -DBOARD_IOTNODE (USART1 PB6/PB7). */
#ifndef BOARD_H
#define BOARD_H
#include <stdint.h>

#ifndef PIL_BAUD
#define PIL_BAUD 115200u
#endif

void board_init(void);
void uart_putc(char c);
void uart_puts(const char *s);
void uart_puthex32(uint32_t v);
void uart_putdec(uint32_t v);

#define DWT_CYCCNT (*(volatile uint32_t *)0xE0001004u)
static inline uint32_t cycles_now(void) { return DWT_CYCCNT; }
#endif
