#!/usr/bin/env python3
"""Plot tone accuracy from the CSV built by tone_stats.py (tests B3, B4).

    python tools/plot_accuracy.py docs/evidence/accuracy.csv --bin-hz 39.06

Top: shown Hz vs set Hz (log axes). Bottom: error in Hz with +/- half a bin
and +/- one bin marked. Electrical and acoustic paths in different series.
Also prints a Markdown table for the report.

Implementation: Claude (Anthropic), to Joe Gould's design and interface;
  reviewed and tested by Joe Gould
"""
import argparse
import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("csv")
ap.add_argument("--bin-hz", type=float, default=40000 / 1024, help="FFT bin width (rate / N)")
ap.add_argument("--out", help="PNG path (default: docs/evidence/plots/<csv name>.png)")
args = ap.parse_args()

with open(args.csv) as fh:
    rows = [r for r in csv.DictReader(fh) if r.get("shown_hz")]
if not rows:
    raise SystemExit("no rows with a shown_hz value")

print("| Path | Set (Hz) | Shown (Hz) | Error (Hz) | Error (%) | Spread (Hz) | Column |")
print("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
for r in sorted(rows, key=lambda r: (r["path"], float(r["set_hz"]))):
    print(f"| {r['path']} | {float(r['set_hz']):.0f} | {float(r['shown_hz']):.1f} | {float(r['error_hz']):+.1f} | "
          f"{float(r['error_pct']):+.2f} | {float(r['spread_hz']):.1f} | {r['peak_col']} |")

fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
for path, marker in (("electrical", "o"), ("acoustic", "s")):
    pts = sorted(((float(r["set_hz"]), float(r["shown_hz"]), float(r["error_hz"])) for r in rows
                  if r["path"] == path))
    if not pts:
        continue
    s, sh, e = zip(*pts)
    a1.plot(s, sh, marker, ls="-", label=path)
    a2.plot(s, e, marker, ls="-", label=path)
lo = min(float(r["set_hz"]) for r in rows)
hi = max(float(r["set_hz"]) for r in rows)
a1.plot([lo, hi], [lo, hi], "k--", lw=0.8, label="ideal")
a1.set_xscale("log")
a1.set_yscale("log")
for ax in (a1.xaxis, a1.yaxis):
    ax.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_minor_formatter(matplotlib.ticker.NullFormatter())
a1.set_ylabel("shown (Hz)")
a1.legend()
a1.set_title("Tone-finder accuracy")
for k, style in ((0.5, ":"), (1.0, "--")):
    a2.axhline(k * args.bin_hz, color="grey", ls=style, lw=0.8)
    a2.axhline(-k * args.bin_hz, color="grey", ls=style, lw=0.8)
a2.set_xlabel("set frequency (Hz)")
a2.set_ylabel("error (Hz)")
a2.text(lo, args.bin_hz, f" ±1 bin ({args.bin_hz:.1f} Hz)", va="bottom", fontsize=8, color="grey")
fig.tight_layout()
out = args.out or os.path.join("docs/evidence/plots", os.path.splitext(os.path.basename(args.csv))[0] + ".png")
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
fig.savefig(out, dpi=130)
print(f"saved {out}")
