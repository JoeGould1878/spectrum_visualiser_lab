/**
 * @file max7219.c
 * @brief MAX7219 chain driver — implementation.
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 * Credits / sources used: MAX7219 datasheet (register map, serial timing:
 * data clocked in on CLK rising edge, MSB first, latched on CS/LOAD rising
 * edge); ESP-IDF v6 SPI master driver documentation. No code adapted.
 *
 * Every write sends one 16-bit (register, value) word per chip in a single
 * CS-low transaction, so all chips latch together on the CS rising edge.
 * Chips not being addressed get NO-OP words.
 */
#include <stdlib.h>
#include <string.h>
#include "max7219.h"
#include "max7219_regs.h"
#include "esp_check.h"

static const char *TAG = "max7219";

struct max7219_dev {
    spi_host_device_t host;
    spi_device_handle_t spi;
    int n_devices;
    uint8_t intensity;   /* last value set, re-sent by max7219_resync() */
};

/*
 * Send one transaction: vals[dev] goes to register reg of chip dev.
 * The first word shifted out ends up in the chip furthest from DIN,
 * so chip n-1 is written first.
 */
static esp_err_t send_row(max7219_handle_t h, uint8_t reg, const uint8_t *vals)
{
    uint8_t buf[MAX7219_MAX_DEVICES * 2];
    for (int dev = 0; dev < h->n_devices; dev++) {
        int pos = (h->n_devices - 1 - dev) * 2;
        buf[pos] = reg;
        buf[pos + 1] = vals[dev];
    }
    spi_transaction_t t = {
        .length = h->n_devices * 16,   /* bits */
        .tx_buffer = buf,
    };
    return spi_device_polling_transmit(h->spi, &t);
}

/* Same (reg, value) to every chip in the chain. */
static esp_err_t send_all(max7219_handle_t h, uint8_t reg, uint8_t val)
{
    uint8_t vals[MAX7219_MAX_DEVICES];
    memset(vals, val, sizeof(vals));
    return send_row(h, reg, vals);
}

esp_err_t max7219_init(const max7219_cfg_t *cfg, max7219_handle_t *out_handle)
{
    ESP_RETURN_ON_FALSE(cfg && out_handle, ESP_ERR_INVALID_ARG, TAG, "null arg");
    ESP_RETURN_ON_FALSE(cfg->n_devices >= 1 && cfg->n_devices <= MAX7219_MAX_DEVICES,
                        ESP_ERR_INVALID_ARG, TAG, "n_devices out of range");
    ESP_RETURN_ON_FALSE(cfg->clock_hz > 0 && cfg->clock_hz <= 10 * 1000 * 1000,
                        ESP_ERR_INVALID_ARG, TAG, "clock_hz must be 1..10 MHz");

    struct max7219_dev *h = calloc(1, sizeof(*h));
    ESP_RETURN_ON_FALSE(h, ESP_ERR_NO_MEM, TAG, "no memory");
    h->host = cfg->host;
    h->n_devices = cfg->n_devices;

    /* At most 16 bytes per transfer, so no DMA needed. */
    spi_bus_config_t bus = {
        .mosi_io_num = cfg->pin_din,
        .miso_io_num = -1,
        .sclk_io_num = cfg->pin_clk,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = MAX7219_MAX_DEVICES * 2,
    };
    esp_err_t err = spi_bus_initialize(cfg->host, &bus, SPI_DMA_DISABLED);
    if (err != ESP_OK) {
        free(h);
        ESP_RETURN_ON_ERROR(err, TAG, "spi_bus_initialize");
    }

    spi_device_interface_config_t dev = {
        .mode = 0,                    /* CPOL 0, CPHA 0: sample on rising edge */
        .clock_speed_hz = cfg->clock_hz,
        .spics_io_num = cfg->pin_cs,  /* driver pulls CS low for the whole word chain */
        .cs_ena_posttrans = 1,        /* hold CS a little after the last clock */
        .queue_size = 1,
    };
    err = spi_bus_add_device(cfg->host, &dev, &h->spi);
    if (err != ESP_OK) {
        spi_bus_free(cfg->host);
        free(h);
        ESP_RETURN_ON_ERROR(err, TAG, "spi_bus_add_device");
    }

    /* Known state: the chips power up in an undefined state (datasheet). */
    err = max7219_clear(h);
    if (err == ESP_OK) err = max7219_resync(h);
    if (err != ESP_OK) {
        max7219_deinit(h);
        ESP_RETURN_ON_ERROR(err, TAG, "chip setup");
    }

    ESP_LOGI(TAG, "%d chips, DIN %d CLK %d CS %d, %d Hz",
             cfg->n_devices, cfg->pin_din, cfg->pin_clk, cfg->pin_cs, cfg->clock_hz);
    *out_handle = h;
    return ESP_OK;
}

esp_err_t max7219_set_intensity(max7219_handle_t h, uint8_t level)
{
    ESP_RETURN_ON_FALSE(h, ESP_ERR_INVALID_ARG, TAG, "null handle");
    if (level > 15) level = 15;
    h->intensity = level;
    return send_all(h, MAX7219_REG_INTENSITY, level);
}

esp_err_t max7219_resync(max7219_handle_t h)
{
    ESP_RETURN_ON_FALSE(h, ESP_ERR_INVALID_ARG, TAG, "null handle");
    ESP_RETURN_ON_ERROR(send_all(h, MAX7219_REG_DISPLAY_TEST, 0x00), TAG, "test");
    ESP_RETURN_ON_ERROR(send_all(h, MAX7219_REG_SCAN_LIMIT, 0x07), TAG, "scan");
    ESP_RETURN_ON_ERROR(send_all(h, MAX7219_REG_DECODE_MODE, 0x00), TAG, "decode");
    ESP_RETURN_ON_ERROR(send_all(h, MAX7219_REG_INTENSITY, h->intensity), TAG, "intensity");
    return send_all(h, MAX7219_REG_SHUTDOWN, 0x01);
}

esp_err_t max7219_shutdown(max7219_handle_t h, bool shutdown)
{
    ESP_RETURN_ON_FALSE(h, ESP_ERR_INVALID_ARG, TAG, "null handle");
    return send_all(h, MAX7219_REG_SHUTDOWN, shutdown ? 0x00 : 0x01);
}

esp_err_t max7219_test_mode(max7219_handle_t h, bool on)
{
    ESP_RETURN_ON_FALSE(h, ESP_ERR_INVALID_ARG, TAG, "null handle");
    return send_all(h, MAX7219_REG_DISPLAY_TEST, on ? 0x01 : 0x00);
}

esp_err_t max7219_clear(max7219_handle_t h)
{
    ESP_RETURN_ON_FALSE(h, ESP_ERR_INVALID_ARG, TAG, "null handle");
    for (int r = 0; r < MAX7219_ROWS_PER_DEVICE; r++) {
        ESP_RETURN_ON_ERROR(send_all(h, MAX7219_REG_DIGIT0 + r, 0x00), TAG, "clear");
    }
    return ESP_OK;
}

esp_err_t max7219_write_all(max7219_handle_t h, const uint8_t *rows)
{
    ESP_RETURN_ON_FALSE(h && rows, ESP_ERR_INVALID_ARG, TAG, "null arg");
    uint8_t vals[MAX7219_MAX_DEVICES];
    for (int r = 0; r < MAX7219_ROWS_PER_DEVICE; r++) {
        for (int dev = 0; dev < h->n_devices; dev++) {
            vals[dev] = rows[dev * MAX7219_ROWS_PER_DEVICE + r];
        }
        ESP_RETURN_ON_ERROR(send_row(h, MAX7219_REG_DIGIT0 + r, vals), TAG, "write row");
    }
    return ESP_OK;
}

void max7219_deinit(max7219_handle_t h)
{
    if (!h) return;
    spi_bus_remove_device(h->spi);
    spi_bus_free(h->host);
    free(h);
}
