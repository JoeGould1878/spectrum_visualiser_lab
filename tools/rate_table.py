#!/usr/bin/env python3
"""Bring-up 02 rate sweep: requested vs measured sample rate (test A2).

    python tools/rate_table.py docs/evidence/logs/2026-10-29_02_rate_sweep.txt

Prints a Markdown table to paste into the report. The measured rate at
40 000 Hz requested goes into APP_SAMPLE_RATE_ACTUAL_HZ.

Implementation: Claude (Anthropic), to Joe Gould's design and interface;
  reviewed and tested by Joe Gould
"""
import argparse
from logparse import parse, need

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("log")
args = ap.parse_args()

log = parse(args.log)
need(log.rate_tests, "RATE_TEST", args.log)

print("| Requested (Hz) | Measured (Hz) | Error | Overflows |")
print("| ---: | ---: | ---: | ---: |")
for r in log.rate_tests:
    err = 100.0 * (r["measured"] - r["requested"]) / r["requested"]
    print(f"| {r['requested']:.0f} | {r['measured']:.0f} | {err:+.2f} % | {r['overflows']} |")

if log.rates:
    print(f"\nStreaming RATE lines: {len(log.rates)}, mean {sum(log.rates) / len(log.rates):.0f} Hz, "
          f"min {min(log.rates):.0f}, max {max(log.rates):.0f}")
