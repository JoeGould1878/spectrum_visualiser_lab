/**
 * @file settings.c
 * @brief NVS settings — implementation.
 *
 * Implementation: Claude (Anthropic), to Joe Gould's design and interface;
 *   reviewed and tested on hardware by Joe Gould
 * Credits / sources used: ESP-IDF NVS documentation (init / erase-and-retry
 *   pattern from the nvs_rw_value example).
 */
#include "settings.h"
#include "app_config.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_check.h"

static const char *TAG = "settings";
#define NVS_NS "spectrum"

esp_err_t settings_init(void)
{
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS partition full or old format: erasing");
        ESP_RETURN_ON_ERROR(nvs_flash_erase(), TAG, "erase");
        err = nvs_flash_init();
    }
    return err;
}

esp_err_t settings_load(settings_t *out)
{
    out->mode = APP_MODE_DEFAULT;
    out->brightness = APP_BRIGHTNESS_DEFAULT;
    out->orient = APP_ORIENT_DEFAULT_K;

    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READONLY, &h);
    if (err == ESP_ERR_NVS_NOT_FOUND) return ESP_OK;   /* nothing saved yet */
    ESP_RETURN_ON_ERROR(err, TAG, "open");

    uint8_t v;
    if (nvs_get_u8(h, "mode", &v) == ESP_OK && v < APP_MODE_COUNT) out->mode = (app_mode_t)v;
    if (nvs_get_u8(h, "bright", &v) == ESP_OK && v <= 15) out->brightness = v;
    if (nvs_get_u8(h, "orient", &v) == ESP_OK && v <= 15) out->orient = v;
    nvs_close(h);
    if (!APP_SHOW_TONE_MODE && out->mode == APP_MODE_TONE_FINDER) out->mode = APP_MODE_FULL;
    ESP_LOGI(TAG, "loaded mode %d, brightness %u, orientation %u", out->mode, out->brightness, out->orient);
    return ESP_OK;
}

esp_err_t settings_save(const settings_t *s)
{
    nvs_handle_t h;
    ESP_RETURN_ON_ERROR(nvs_open(NVS_NS, NVS_READWRITE, &h), TAG, "open");
    esp_err_t err = nvs_set_u8(h, "mode", (uint8_t)s->mode);
    if (err == ESP_OK) err = nvs_set_u8(h, "bright", s->brightness);
    if (err == ESP_OK) err = nvs_set_u8(h, "orient", s->orient);
    if (err == ESP_OK) err = nvs_commit(h);
    nvs_close(h);
    return err;
}
