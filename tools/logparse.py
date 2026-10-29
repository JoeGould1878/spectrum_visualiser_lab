"""Parse serial logs from the firmware and bring-ups.

Line formats are defined in main/debug_stream.h. Any other line (ESP_LOG
output, boot messages) is ignored, so a raw `idf.py monitor | tee` capture
can be passed straight in.

Implementation: Claude (Anthropic), to Joe Gould's design and interface;
  reviewed and tested by Joe Gould
"""
import re
import sys
from dataclasses import dataclass, field

ANSI = re.compile(r"\x1b\[[0-9;]*m")
MODES = {0: "full", 1: "bass/voice", 2: "tone finder", 3: "linear"}
STATUS_BITS = {1: "silent", 2: "clipping", 4: "above range", 8: "not listening"}


@dataclass
class Log:
    frames: list = field(default_factory=list)      # dict: seq, t_ms, mode, status, process_us, cols[]
    tones: list = field(default_factory=list)       # dict: seq, hz, db
    rates: list = field(default_factory=list)       # float Hz
    display: list = field(default_factory=list)     # dict: fps, age_avg_ms, age_max_ms, write_us
    raw: list = field(default_factory=list)         # list of int lists
    stats: list = field(default_factory=list)       # dict: mean, min, max, rms
    rate_tests: list = field(default_factory=list)  # dict: requested, measured, overflows
    config: str = ""                                # boot "config:" line, if present
    bad_lines: int = 0                              # tagged lines that didn't parse (cut off etc.)


def _nums(parts, conv=float):
    return [conv(p) for p in parts]


def parse(path):
    log = Log()
    with open(path, errors="replace") as fh:
        for line in fh:
            line = ANSI.sub("", line).strip()
            if "config:" in line and not log.config:
                log.config = line[line.index("config:"):]
            tag, _, rest = line.partition(",")
            parts = rest.split(",") if rest else []
            try:
                if tag == "FRAME":
                    seq, t_ms, mode, status, proc = _nums(parts[:5], int)
                    log.frames.append(dict(seq=seq, t_ms=t_ms, mode=mode, status=status,
                                           process_us=proc, cols=_nums(parts[5:])))
                elif tag == "TONE":
                    log.tones.append(dict(seq=int(parts[0]), hz=float(parts[1]), db=float(parts[2])))
                elif tag == "RATE":
                    log.rates.append(float(parts[0]))
                elif tag == "DISPLAY":
                    fps, avg, mx, wr = _nums(parts[:4])
                    log.display.append(dict(fps=fps, age_avg_ms=avg, age_max_ms=mx, write_us=wr))
                elif tag == "RAW":
                    n = int(parts[0])
                    vals = _nums(parts[1:], int)
                    if len(vals) == n:
                        log.raw.append(vals)
                    else:
                        log.bad_lines += 1
                elif tag == "STATS":
                    mean, lo, hi, rms = _nums(parts[:4])
                    log.stats.append(dict(mean=mean, min=lo, max=hi, rms=rms))
                elif tag == "RATE_TEST":
                    req, meas, ovf = _nums(parts[:3])
                    log.rate_tests.append(dict(requested=req, measured=meas, overflows=int(ovf)))
            except (ValueError, IndexError):
                log.bad_lines += 1
    return log


def status_names(bits):
    return [name for bit, name in STATUS_BITS.items() if bits & bit] or ["ok"]


def need(items, what, path):
    if not items:
        sys.exit(f"{path}: no {what} lines found — is this the right log?")
