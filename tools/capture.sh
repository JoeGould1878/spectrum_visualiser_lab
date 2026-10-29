#!/usr/bin/env bash
# Capture a serial log as dated evidence.
#   tools/capture.sh 02_gain40_quiet          -> docs/evidence/logs/<today>_02_gain40_quiet.txt
#   tools/capture.sh B1_quiet_room /dev/ttyACM1
# Run from the repo root or a bring-up folder; Ctrl+] stops.
# Implementation: Claude (Anthropic), to Joe Gould's design and interface; tested by Joe Gould
set -euo pipefail
name=${1:?usage: capture.sh <test_name> [port]}
port=${2:-/dev/ttyACM0}
root=$(git rev-parse --show-toplevel)
out="$root/docs/evidence/logs/$(date +%F)_${name}.txt"
if [[ -e "$out" ]]; then
    echo "$out already exists — pick another name" >&2
    exit 1
fi
echo "Logging to $out  (Ctrl+] to stop)"
idf.py -p "$port" monitor | tee "$out"
