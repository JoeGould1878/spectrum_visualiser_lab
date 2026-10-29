#!/usr/bin/env python3
"""Main-firmware log summary + column heatmap (tests B1, B2, and any FRAME log).

    python tools/frames.py docs/evidence/logs/2026-11-03_quiet_room.txt

Prints: config line, frame rate (R4), processing time, sample rate,
display refresh / frame age / SPI write time (latency budget, R3), how often
each status flag was on, and per-column levels. For a quiet-room log the
column levels give APP_FLOOR_DB (suggested value printed).
Saves a heatmap (time x column, dB) to docs/evidence/plots/.

Implementation: Claude (Anthropic), to Joe Gould's design and interface;
  reviewed and tested by Joe Gould
"""
import argparse
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from logparse import parse, need, MODES, STATUS_BITS

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("log")
ap.add_argument("--out", help="PNG path (default: docs/evidence/plots/<log name>_frames.png)")
ap.add_argument("--db-per-row", type=float, default=4.0, help="APP_DB_PER_ROW, for the floor suggestion")
args = ap.parse_args()

log = parse(args.log)
need(log.frames, "FRAME", args.log)
fr = log.frames
cols = np.array([f["cols"] for f in fr if len(f["cols"]) == len(fr[0]["cols"])])
t_s = np.array([f["t_ms"] for f in fr]) / 1000.0
seq = np.array([f["seq"] for f in fr])
proc = np.array([f["process_us"] for f in fr])

print(f"# {os.path.basename(args.log)}")
if log.config:
    print(log.config)
modes = sorted({f["mode"] for f in fr})
print(f"frames: {len(fr)} over {t_s[-1] - t_s[0]:.1f} s, mode(s): {', '.join(MODES.get(m, str(m)) for m in modes)}")
if len(fr) > 1:
    dur = t_s[-1] - t_s[0]
    print(f"analysed frame rate: {(seq[-1] - seq[0]) / dur:.1f} /s  (R4 needs >= 20)"
          f"; FRAME lines logged: {len(fr) / dur:.1f} /s")
    missing = (seq[-1] - seq[0] + 1) - len(fr)
    if missing > 0:
        print(f"  {missing} frames not in the log (APP_DEBUG_EVERY_N_FRAMES > 1, or lost lines)")
print(f"processing (FFT + mapping): median {np.median(proc):.0f} us, max {proc.max():.0f} us")
if log.rates:
    print(f"sample rate: mean {np.mean(log.rates):.0f} Hz ({len(log.rates)} RATE lines)")
if log.display:
    d = log.display
    print(f"display: {np.mean([x['fps'] for x in d]):.1f} fps, frame age avg {np.mean([x['age_avg_ms'] for x in d]):.1f} ms"
          f" / max {max(x['age_max_ms'] for x in d):.1f} ms, SPI write max {max(x['write_us'] for x in d):.0f} us")
print("status flags on (% of frames): " + ", ".join(
    f"{name} {100 * np.mean([(f['status'] & bit) != 0 for f in fr]):.0f}%" for bit, name in STATUS_BITS.items()))
if log.bad_lines:
    print(f"({log.bad_lines} tagged lines could not be parsed — usually cut off at start/end)")

# Per-column levels
med = np.median(cols, axis=0)
p95 = np.percentile(cols, 95, axis=0)
print("\ncolumn levels (dBFS):\n  col  median    p95")
for c in range(cols.shape[1]):
    print(f"  {c:3d}  {med[c]:6.1f}  {p95[c]:6.1f}")
floor = float(np.max(p95))
print(f"\nquiet-room use: loudest column (col {int(np.argmax(p95))}) p95 = {floor:.1f} dB. Setting APP_FLOOR_DB to about "
      f"{floor + 1:.0f} keeps 95 % of quiet frames below the first row (R5);")
print(f"with {args.db_per_row} dB/row the top row is then {floor + 1 + 8 * args.db_per_row:.0f} dBFS.")

fig, ax = plt.subplots(figsize=(10, 4.5))
im = ax.imshow(cols.T, aspect="auto", origin="lower", cmap="viridis",
               extent=[0, t_s[-1] - t_s[0], -0.5, cols.shape[1] - 0.5])
ax.set_xlabel("time (s)")
ax.set_ylabel("display column (0 = lowest frequency)")
ax.set_title(os.path.basename(args.log))
fig.colorbar(im, ax=ax, label="dBFS")
fig.tight_layout()
out = args.out or os.path.join("docs/evidence/plots", os.path.splitext(os.path.basename(args.log))[0] + "_frames.png")
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
fig.savefig(out, dpi=130)
print(f"saved {out}")
