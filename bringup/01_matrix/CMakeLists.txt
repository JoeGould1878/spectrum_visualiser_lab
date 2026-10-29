# Bring-up 01 — MAX7219 32x8 matrix: driver check + orientation.
# Uses the real max7219 and frame_gfx components from the main project.
cmake_minimum_required(VERSION 3.16)

set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_LIST_DIR}/../../components/max7219"
    "${CMAKE_CURRENT_LIST_DIR}/../../components/frame_gfx"
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(bringup_01_matrix)
