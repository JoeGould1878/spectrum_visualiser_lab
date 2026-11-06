# KiCad schematic

`spectrum_visualiser.kicad_sch`: the full build (one-stage LM358 preamp, supply filter, LED module header, buttons). The ESP32-S3 pins are global labels; the pin table on the sheet says which pin each one is. KiCad 7 format, so it opens in KiCad 7, 8 and 9 (newer versions offer to upgrade the file).

- `spectrum_visualiser.pdf` / `.png`: exported from KiCad, for the report.
- `spectrum.kicad_sym` + `sym-lib-table`: project library with one symbol, `+3V3_MIC` (the filtered preamp rail). KiCad names a power net after the symbol's pin, so a renamed `+3V3` would merge with the board 3V3.
- `gen_kicad_sch.py`: the script that writes the schematic from KiCad's standard symbol library. If you edit the schematic in KiCad, don't re-run the script, or it will overwrite your edits.

Checked with `kicad-cli sch export netlist`: every net matches the circuit (R0 between `+3V3` and `+3V3_MIC`; U1A pins 1/2/3; U1B pins 6–7 tied and pin 5 to GND; GPIO labels on J1, SW1, SW2, and R6/C4).
