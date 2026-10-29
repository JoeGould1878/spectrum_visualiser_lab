# Tools (laptop side)

Python scripts for turning serial logs into evidence. None written yet — add them as tests need them.

Planned:

| Script | Input | Output |
| --- | --- | --- |
| `capture.sh` | serial port, test name | `docs/evidence/logs/<date>_<name>.txt` via `idf.py monitor \| tee` |
| `plot_raw.py` | `RAW,` lines | waveform plot + mean/min/max (bring-up 02) |
| `plot_spectrum.py` | `FRAME,` lines | column levels over time (heatmap) |
| `accuracy.py` | `TONE,` lines + the tone list played | input Hz vs shown Hz table, error |
| `response.py` | sweep log | frequency-response chart |

Line formats are defined in `main/debug_stream.h`.

Set up once:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install numpy matplotlib pandas
```
