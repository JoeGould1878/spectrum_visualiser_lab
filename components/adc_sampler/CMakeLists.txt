idf_component_register(
    SRCS "adc_sampler.c"
    INCLUDE_DIRS "include"
    PRIV_REQUIRES esp_adc esp_timer
)
