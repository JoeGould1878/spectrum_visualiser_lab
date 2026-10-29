#!/usr/bin/env python3
"""Tone accuracy for one test tone: shown Hz vs set Hz, appended to a CSV (tests B3, B4).

Record one log per tone (a few seconds each), then for each:

    python tools/tone_stats.py LOG --set-hz 440 --path electrical --csv docs/evidence/accuracy.csv

Prints median shown Hz, error, spread, and which column was loudest; appends
one row to the CSV. Then plot all rows with plot_accuracy.py.

Implementation: Claude (Anthropic), to Joe Gould's design and interface;
  reviewed and tested by Joe Gould
"""
import argparse
import csv
import os
import numpy as np
from logparse import parse, need

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("log")
ap.add_argument("--set-hz", type=float, required=True, help="frequency set on the generator / phone")
ap.add_argument("--path", default="electrical", help="electrical | acoustic (label in the CSV)")
ap.add_argument("--csv", help="append a result row to this CSV")
ap.add_argument("--skip-s", type=float, default=0.5, help="ignore the first N seconds (settling)")
args = ap.parse_args()

log = parse(args.log)
need(log.frames, "FRAME", args.log)
t0 = log.frames[0]["t_ms"]
keep = {f["seq"] for f in log.frames if f["t_ms"] - t0 >= args.skip_s * 1000}
frames = [f for f in log.frames if f["seq"] in keep]
tones = [t for t in log.tones if t["seq"] in keep]

valid_pct = 100.0 * len(tones) / max(len(frames), 1)
peak_cols = [int(np.argmax(f["cols"])) for f in frames]
col_mode = max(set(peak_cols), key=peak_cols.count) if peak_cols else -1
col_share = 100.0 * peak_cols.count(col_mode) / max(len(peak_cols), 1)

row = dict(set_hz=args.set_hz, path=args.path, log=os.path.basename(args.log), frames=len(frames),
           valid_pct=round(valid_pct, 1), peak_col=col_mode, peak_col_pct=round(col_share, 1))
if tones:
    hz = np.array([t["hz"] for t in tones])
    db = np.array([t["db"] for t in tones])
    med = float(np.median(hz))
    row.update(shown_hz=round(med, 2), error_hz=round(med - args.set_hz, 2),
               error_pct=round(100 * (med - args.set_hz) / args.set_hz, 3),
               spread_hz=round(float(np.percentile(hz, 95) - np.percentile(hz, 5)), 2),
               level_db=round(float(np.median(db)), 1))
    print(f"set {args.set_hz:.1f} Hz -> shown {med:.1f} Hz (error {med - args.set_hz:+.1f} Hz, "
          f"{row['error_pct']:+.2f} %), 5-95 % spread {row['spread_hz']:.1f} Hz, level {row['level_db']} dBFS")
else:
    print(f"set {args.set_hz:.1f} Hz -> no tone found (below APP_TONE_MIN_DB?)")
print(f"tone found in {valid_pct:.0f} % of {len(frames)} frames; loudest column {col_mode} in {col_share:.0f} % of frames")

if args.csv:
    fields = ["set_hz", "path", "shown_hz", "error_hz", "error_pct", "spread_hz", "level_db",
              "peak_col", "peak_col_pct", "valid_pct", "frames", "log"]
    new = not os.path.exists(args.csv)
    os.makedirs(os.path.dirname(args.csv) or ".", exist_ok=True)
    with open(args.csv, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})
    print(f"appended to {args.csv}")
