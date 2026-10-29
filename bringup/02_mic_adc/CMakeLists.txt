# Bring-up 02 — MAX9814 mic into the ESP32-S3 continuous ADC:
# raw samples over serial + measured sample rate.
cmake_minimum_required(VERSION 3.16)

set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_LIST_DIR}/../../components/adc_sampler"
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(bringup_02_mic_adc)
