idf_component_register(
    SRCS
        "main.c"
        "audio_task.c"
        "display_task.c"
        "input_task.c"
        "settings.c"
        "debug_stream.c"
    INCLUDE_DIRS "."
    PRIV_REQUIRES
        adc_sampler spectrum band_map bar_model tone_finder frame_gfx max7219 button
        nvs_flash esp_timer
)
