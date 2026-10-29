idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "."
    PRIV_INCLUDE_DIRS "../../../main"   # app_config.h only: pins and display settings
    PRIV_REQUIRES max7219 frame_gfx esp_timer
)
