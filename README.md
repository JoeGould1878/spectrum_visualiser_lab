# Spectrum Visualiser

Audio-reactive spectrum display on a 32 × 8 LED matrix — Mini-Challenge 2 (CDIO), 2026.

A MAX9814 microphone feeds an ESP32-S3; the firmware samples it continuously, takes an FFT and shows the spectrum as 32 bars. The aim is an *honest* display for a teaching lab: a tone you play lands in the right column, and the display says when it can't be trusted (silence, clipping, out of range).

**Status:** skeleton only — headers, build files and docs. Implementation is written one component at a time. See [`docs/CONTEXT.md`](docs/CONTEXT.md) for where things are and [`docs/PLAN.md`](docs/PLAN.md) for the Conceive/Design plan.

## Hardware

| Part | Notes |
| --- | --- |
| Freenove ESP32-S3-WROOM | camera ribbon unplugged |
| MAX9814 electret mic module | AGC; 1.25 V bias output; powered from 3.3 V |
| 4-in-1 MAX7219 LED matrix (32 × 8) | 5 V |
| Push buttons × 2 | mode, listen on/off |

Pins: [`main/app_config.h`](main/app_config.h). Wiring per part: [`bringup/README.md`](bringup/README.md).

## Layout

```
spectrum_visualiser/
├── CMakeLists.txt, sdkconfig.defaults   ESP-IDF project
├── main/                application: tasks, config, settings, debug stream
├── components/
│   ├── max7219/         SPI LED-matrix driver
│   ├── adc_sampler/     ESP32-S3 continuous (DMA) ADC
│   ├── spectrum/        DC removal, decimation, window, FFT (esp-dsp)
│   ├── band_map/        FFT bins -> 32 columns (linear / hybrid log)   [pure C]
│   ├── bar_model/       dB -> bar height, smoothing, peak dots         [pure C]
│   ├── tone_finder/     strongest frequency in Hz                      [pure C]
│   ├── frame_gfx/       32x8 drawing, text, matrix orientation         [pure C]
│   └── button/          debounced buttons
├── bringup/             standalone hardware tests (01 matrix, 02 mic + ADC)
├── host_tests/          laptop tests for the [pure C] components (make)
├── tools/               Python scripts for logs -> plots (planned)
└── docs/                plan, running context, brief, evidence
```

Signal path: `adc_sampler → spectrum → band_map → (tone_finder) → bar_model → frame_gfx → max7219`.

## Build

```bash
. $IDF_PATH/export.sh          # or your get_idf alias
idf.py set-target esp32s3      # first time only
idf.py build flash -p /dev/ttyACM0 monitor
```

Laptop tests (no board needed):

```bash
cd host_tests && make
```

## Credits and sources

- Brief: Mini-Challenge 2, Audio-Reactive Spectrum Visualiser (W. Al-Nuaimy, H. van Zalinge, 2026) — `docs/brief/`
- Previous prototypes, used as reference (no code reused): [Aidan Gan's project blog](https://aidangan.blogspot.com/2026/06/spectrum-visualiser-project-week-1-this.html), [Casey Overkleeft's Lab-in-a-Box blog](https://labinaboxcaseyov.blogspot.com/2026/06/day-1-spectrum-visualiser-research-and.html) (summarising Zhexi Zhang's report)
- [esp-dsp](https://components.espressif.com/components/espressif/esp-dsp) (Espressif) for the FFT
- ESP-IDF ADC continuous-mode documentation and examples
- AI assistance: Claude (Anthropic) for planning, project skeleton and firmware implementation; the team specified, tested and evaluated it on hardware

Any further code or ideas adapted are credited in the header of the file that uses them.
