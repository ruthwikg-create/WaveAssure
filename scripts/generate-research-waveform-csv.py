"""Generate de-identified deterministic *synthetic* waveform CSV for import smoke tests.

These are not patient data, clinically plausible signals, validated rhythms or
actual alarm events. Never treat this sample as a medical measurement.
"""
from __future__ import annotations
import argparse
import csv
import math
from pathlib import Path


def write_example(destination: Path, *, rate: int = 100, seconds: int = 20) -> Path:
    if not (50 <= rate <= 1000) or not (2 <= seconds <= 600):
        raise ValueError("Use 50-1000 Hz and 2-600 seconds for this example")
    if rate * seconds > 100000:
        raise ValueError("Generated sample count exceeds WaveAssure's 100000-sample limit")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        out = csv.writer(handle)
        out.writerow(["time_s", "ECG_mV", "PPG_au", "ABP_mmHg"])
        for index in range(rate * seconds):
            t = index / rate
            # Engineering sine-wave fixtures, not modeled human physiology.
            ecg = 0.2 * math.sin(2 * math.pi * 1.2 * t) + 0.03 * math.sin(2 * math.pi * 12 * t)
            ppg = 0.5 + 0.15 * math.sin(2 * math.pi * 1.2 * (t - 0.2))
            abp = 90.0 + 13 * math.sin(2 * math.pi * 1.2 * (t - 0.3))
            out.writerow([f"{t:.5f}", f"{ecg:.6f}", f"{ppg:.6f}", f"{abp:.6f}"])
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic CSV for WaveAssure UI import only")
    parser.add_argument("--output", default="waveassure-demo-waveforms.csv")
    args = parser.parse_args()
    target = write_example(Path(args.output))
    print(f"Generated synthetic, nonclinical waveform fixture: {target.resolve()}")
