/**
 * @file max7219_regs.h
 * @brief MAX7219 register map (private to this component).
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
 *
 * Every SPI transfer to one chip is 16 bits: [address (8)] [data (8)].
 * For a chain of N chips, shift N x 16 bits while CS is low, then raise CS:
 * the first 16 bits sent end up in the chip furthest from DIN.
 *
 * Source: MAX7219 datasheet, register address map.
 */
#pragma once

#define MAX7219_REG_NOOP         0x00
#define MAX7219_REG_DIGIT0       0x01   /* DIGIT1..7 = 0x02..0x08 (rows 1..7) */
#define MAX7219_REG_DECODE_MODE  0x09   /* 0x00 = no BCD decode (matrix use) */
#define MAX7219_REG_INTENSITY    0x0A   /* 0x00..0x0F */
#define MAX7219_REG_SCAN_LIMIT   0x0B   /* 0x07 = scan all 8 rows */
#define MAX7219_REG_SHUTDOWN     0x0C   /* 0x00 = shutdown, 0x01 = normal */
#define MAX7219_REG_DISPLAY_TEST 0x0F   /* 0x01 = all LEDs on */
