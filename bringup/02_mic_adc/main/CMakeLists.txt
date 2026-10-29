idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "."
    PRIV_INCLUDE_DIRS "../../../main"   # app_config.h only: pin and rate
    PRIV_REQUIRES adc_sampler esp_timer
)
