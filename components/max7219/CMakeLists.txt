idf_component_register(
    SRCS "max7219.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_driver_spi      # spi_host_device_t appears in the public header
    PRIV_REQUIRES esp_driver_gpio
)
