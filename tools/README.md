# Tools (laptop side)

Python scripts that turn serial logs into evidence (tables to paste into the report, plots in `docs/evidence/plots/`).
Line formats are defined in `main/debug_stream.h`; any other line in a log is ignored, so raw `idf.py monitor` captures work as they are.

Set up once (from the repo root):

```bash
python3 -m venv .venv && .venv/bin/pip install numpy matplotlib
source .venv/bin/activate      # each new terminal
```

| Script | Test | Input | Output |
| --- | --- | --- | --- |
| `capture.sh <name>` | all | serial port | `docs/evidence/logs/<today>_<name>.txt` (refuses to overwrite) |
| `rate_table.py LOG` | A2 | `RATE_TEST` lines | requested vs measured rate table → `APP_SAMPLE_RATE_ACTUAL_HZ` |
| `plot_raw.py LOG` | A2 | `RAW`, `STATS` | bias / clipping / noise summary; waveform + spectrum plot |
| `frames.py LOG` | B1, B2, any | `FRAME`, `RATE`, `DISPLAY` | frame rate, processing time, latency stats, status-flag %, per-column levels, suggested `APP_FLOOR_DB`; heatmap |
| `tone_stats.py LOG --set-hz F --path electrical --csv docs/evidence/accuracy.csv` | B3, B4 | `FRAME`, `TONE` | shown vs set Hz for one tone; appends a CSV row |
| `plot_accuracy.py docs/evidence/accuracy.csv` | B3, B4 | that CSV | accuracy table + plot (error vs ±½ and ±1 bin) |

Examples:

```bash
tools/capture.sh 02_gain40_tone1k                       # Ctrl+] to stop
python tools/plot_raw.py docs/evidence/logs/2026-10-29_02_gain40_tone1k.txt
python tools/frames.py docs/evidence/logs/2026-11-03_B1_quiet_room.txt
for f in 100 200 440 1000 2000 5000 7500; do      # one log per tone, named ..._B3_tone<f>.txt
  python tools/tone_stats.py docs/evidence/logs/2026-11-03_B3_tone$f.txt --set-hz $f --csv docs/evidence/accuracy.csv
done
python tools/plot_accuracy.py docs/evidence/accuracy.csv
```

Implementation: Claude (Anthropic), to Joe Gould's design and interface; reviewed and tested by Joe Gould.
