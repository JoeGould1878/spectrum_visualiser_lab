#!/usr/bin/env python3
"""Bring-up 02 mic check: waveform + spectrum of one RAW frame, STATS summary (test A2).

    python tools/plot_raw.py docs/evidence/logs/2026-10-29_02_gain40_tone1k.txt
    python tools/plot_raw.py LOG --frame 3 --rate 39800 --out docs/evidence/plots/x.png

Prints mean (bias), min/max (clipping?) and rms (noise / signal level) over
the whole log; plots one frame in raw counts and approximate volts, and its
spectrum so a 1 kHz tone shows as one peak. Default output: next to the log
name in docs/evidence/plots/.

Implementation: Claude (Anthropic), to Joe Gould's design and interface;
  reviewed and tested by Joe Gould
"""
import argparse
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from logparse import parse, need

VOLTS_PER_COUNT = 3.1 / 4095   # ~12 dB attenuation range on the S3; approximate (uncalibrated)

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("log")
ap.add_argument("--frame", type=int, default=-1, help="which RAW frame (default: last)")
ap.add_argument("--rate", type=float, help="sample rate in Hz (default: mean RATE line, else 40000)")
ap.add_argument("--out", help="PNG path (default: docs/evidence/plots/<log name>.png)")
args = ap.parse_args()

log = parse(args.log)
need(log.raw, "RAW", args.log)
rate = args.rate or (np.mean(log.rates) if log.rates else 40000.0)

if log.stats:
    mean = np.array([s["mean"] for s in log.stats])
    rms = np.array([s["rms"] for s in log.stats])
    print(f"STATS over {len(log.stats)} frames:")
    print(f"  bias (mean)  {mean.mean():7.1f} counts  (~{mean.mean() * VOLTS_PER_COUNT:.2f} V)")
    print(f"  min / max    {min(s['min'] for s in log.stats):7.0f} / {max(s['max'] for s in log.stats):.0f} counts"
          "  (near 0 or 4095 = clipping)")
    print(f"  rms          median {np.median(rms):.1f}, max {rms.max():.1f} counts")

x = np.array(log.raw[args.frame], dtype=float)
t_ms = np.arange(len(x)) / rate * 1000
ac = x - x.mean()
win = np.hanning(len(ac))
spec = np.abs(np.fft.rfft(ac * win)) * 2 / (len(ac) * win.mean() * 2048)
freqs = np.fft.rfftfreq(len(ac), 1 / rate)
db = 20 * np.log10(np.maximum(spec, 1e-7))
peak = int(np.argmax(db[1:])) + 1
print(f"Frame {args.frame}: rms {ac.std():.1f} counts, strongest {freqs[peak]:.0f} Hz at {db[peak]:.1f} dBFS "
      f"(nearest bin, ±{rate / len(ac) / 2:.0f} Hz; rate {rate:.0f} Hz)")

fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.5))
a1.plot(t_ms, x, lw=0.8)
a1.set_xlabel("time (ms)")
a1.set_ylabel("raw ADC counts")
a1.set_ylim(0, 4095)
a1.axhline(x.mean(), ls="--", lw=0.8, color="grey")
sec = a1.secondary_yaxis("right", functions=(lambda c: c * VOLTS_PER_COUNT, lambda v: v / VOLTS_PER_COUNT))
sec.set_ylabel("≈ volts")
a1.set_title(os.path.basename(args.log))
a2.plot(freqs / 1000, db, lw=0.8)
a2.set_xlabel("frequency (kHz)")
a2.set_ylabel("dBFS (0 = full-scale sine)")
a2.set_ylim(max(db.min(), -120), 5)
a2.annotate(f"{freqs[peak]:.0f} Hz", (freqs[peak] / 1000, db[peak]), textcoords="offset points", xytext=(5, -10))
fig.tight_layout()

out = args.out or os.path.join("docs/evidence/plots", os.path.splitext(os.path.basename(args.log))[0] + ".png")
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
fig.savefig(out, dpi=130)
print(f"saved {out}")
