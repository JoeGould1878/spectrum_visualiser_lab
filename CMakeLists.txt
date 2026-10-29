# Spectrum Visualiser — ESP-IDF project file
# Build:  idf.py set-target esp32s3   (once)
#         idf.py build flash monitor
cmake_minimum_required(VERSION 3.16)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(spectrum_visualiser)
