/**
 * @file max7219.h
 * @brief Driver for a chain of MAX7219 8x8 LED matrix modules over SPI.
 *
 * Design and interface: Joe Gould, drafted with Claude (Anthropic)
 *
 * Our display is a 4-in-1 module (4 chips daisy-chained = 32 x 8 pixels).
 * This driver only knows about chips and their 8 "digit" registers (rows);
 * it does not know which way round the module is mounted. Turning a
 * 32-column picture into per-chip rows is frame_gfx's job
 * (frame_gfx_to_device_rows), so orientation is fixed in one place.
 *
 * Wiring (see main/app_config.h): DIN = MOSI, CLK = SCLK, CS = LOAD.
 * The chips run at 5 V; the ESP32-S3 drives 3.3 V logic, which is below the
 * MAX7219's 3.5 V input-high spec. Check for glitches at bring-up 01.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"
#include "driver/spi_master.h"

#ifdef __cplusplus
extern "C" {
#endif

#define MAX7219_ROWS_PER_DEVICE 8
#define MAX7219_MAX_DEVICES     8

typedef struct {
    spi_host_device_t host;   /**< e.g. SPI2_HOST */
    int pin_din;              /**< MOSI */
    int pin_clk;              /**< SCLK */
    int pin_cs;               /**< LOAD / CS */
    int n_devices;            /**< chips in the chain (4 for our module) */
    int clock_hz;             /**< SPI clock; MAX7219 max is 10 MHz, start lower */
} max7219_cfg_t;

/** Opaque handle (struct defined in max7219.c). */
typedef struct max7219_dev *max7219_handle_t;

/**
 * Set up the SPI bus and device, then put every chip in a known state:
 * test mode off, scan limit 8 rows, no decode, display cleared, out of shutdown.
 */
esp_err_t max7219_init(const max7219_cfg_t *cfg, max7219_handle_t *out_handle);

/** Brightness 0..15 for every chip. */
esp_err_t max7219_set_intensity(max7219_handle_t h, uint8_t level);

/** true = shutdown (display off, low power), false = normal operation. */
esp_err_t max7219_shutdown(max7219_handle_t h, bool shutdown);

/** true = all LEDs on at full brightness (hardware test mode). */
esp_err_t max7219_test_mode(max7219_handle_t h, bool on);

/** Blank every chip. */
esp_err_t max7219_clear(max7219_handle_t h);

/**
 * Write all 8 rows of every chip in one go.
 * @param rows  n_devices * 8 bytes: rows[dev * 8 + r] is row r of chip dev,
 *              bit 7..0 = the 8 LEDs of that row. Chip 0 = the one nearest DIN.
 */
esp_err_t max7219_write_all(max7219_handle_t h, const uint8_t *rows);

/**
 * Re-send every control register (test mode off, scan limit, no decode,
 * last intensity, out of shutdown). A glitch on the 3.3 V data line can flip
 * one of these and leave the display wrong until reset; calling this every
 * second or so recovers. A mitigation, not a fix: count glitches first.
 */
esp_err_t max7219_resync(max7219_handle_t h);

/** Release the SPI device and bus. */
void max7219_deinit(max7219_handle_t h);

#ifdef __cplusplus
}
#endif
