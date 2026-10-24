"""Deterministic physiological signal processing. Not medical diagnosis."""
from __future__ import annotations
import math
import numpy as np
from scipy.signal import butter, sosfiltfilt, find_peaks, welch
from .schemas import RecordCreate, Channel, FaultRequest


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(a * a))) if a.size else 0.0


def _mains_ratio(x: np.ndarray, fs: float) -> float | None:
    # Technical 50 Hz contamination indicator, not a validated diagnostic feature.
    if fs < 115 or len(x) < max(256, int(fs*3)):
        return None
    frequencies, power = welch(x, fs=fs, nperseg=min(2048, len(x)))
    band = (frequencies >= 5) & (frequencies <= min(58, fs/2 - 1))
    mains = (frequencies >= 48) & (frequencies <= 52)
    total = float(power[band].sum())
    return round(float(power[mains].sum())/total, 4) if total > 1e-12 else 0.0


def analyze_channel(channel: Channel, fs: float) -> dict:
    data = np.array([np.nan if s is None else s for s in channel.samples], dtype=float)
    missing = ~np.isfinite(data)
    missing_fraction = float(missing.mean())
    usable = data[~missing]
    if not len(usable):
        return dict(kind=channel.kind, name=channel.name, unit=channel.unit, quality="unusable", reasons=["No finite samples"], missing_pct=100., span=0., stddev=0., mains_ratio=None, estimated_bpm=None, bpm_method=None)
    std = float(usable.std())
    span = float(np.ptp(usable))
    reasons = []
    if missing_fraction >= 0.02:
        reasons.append("Missing sample fraction >= 2%")
    if std < {"ECG": 0.01, "PPG": 0.005, "ABP": 0.15}[channel.kind]:
        reasons.append("Nearly flat signal")
    # Constant extreme plateaus can indicate clipping. Only flag after variation exists.
    extreme = (np.isclose(usable, usable.max(), rtol=0, atol=max(span*0.00001, 1e-8)) |
               np.isclose(usable, usable.min(), rtol=0, atol=max(span*0.00001, 1e-8)))
    clipping_fraction = float(extreme.mean()) if span > 1e-9 else 0.0
    if span > 1e-6 and clipping_fraction > 0.08:
        reasons.append("Repeated extrema suggest possible clipping")
    interpolated = data.copy()
    if missing.any() and len(usable) > 1:
        ix = np.arange(len(data))
        interpolated[missing] = np.interp(ix[missing], ix[~missing], usable)
    elif missing.any():
        interpolated[missing] = usable[0]
    mains_ratio = _mains_ratio(interpolated, fs)
    if mains_ratio is not None and mains_ratio > 0.22:
        reasons.append("Strong 50 Hz spectral component")
    quality = "review" if reasons else "passes_technical_checks"
    bpm = None
    if channel.kind == "ECG" and not reasons and len(data) >= int(fs*4):
        try:
            sos = butter(2, [2, min(35, fs*.43)], btype="bandpass", fs=fs, output="sos")
            filtered = sosfiltfilt(sos, interpolated)
            prominence = max(float(np.ptp(filtered))*.3, float(np.std(filtered))*.8)
            peaks, _ = find_peaks(filtered, prominence=prominence, distance=int(fs*.31))
            if len(peaks) >= 3:
                intervals = np.diff(peaks)/fs
                med = float(np.median(intervals))
                if 0.27 <= med <= 2.0:
                    bpm = round(60/med, 1)
        except ValueError:
            pass
    return dict(kind=channel.kind, name=channel.name, unit=channel.unit, quality=quality,
                reasons=reasons, missing_pct=round(missing_fraction*100, 2),
                span=round(span, 4), stddev=round(std, 4),
                possible_clipping_pct=round(clipping_fraction*100, 2),
                mains_ratio=mains_ratio, estimated_bpm=bpm,
                bpm_method="research ECG peak-interval heuristic; not validated" if bpm is not None else None)


def analyze(record: RecordCreate) -> dict:
    channels = [analyze_channel(c, record.sample_rate_hz) for c in record.channels]
    # A prototype peak detector must not expose an apparent patient heart rate
    # on real data without analytical validation. This applies to the API, not
    # just the UI. Research feature extraction is a separate offline function.
    if record.origin == "wfdb_research":
        for item in channels:
            item["estimated_bpm"] = None
            item["bpm_method"] = None
    status = "REVIEW_REQUIRED" if any(c["quality"] != "passes_technical_checks" for c in channels) else "TECHNICAL_CHECKS_PASSED"
    return dict(status=status, quality_checks=channels, duration_s=round(len(record.channels[0].samples)/record.sample_rate_hz, 3),
                warning="Research-only signal quality checks. Not a diagnosis, validated alarm classifier, or clinical alarm status.",
                alarm_classification={"status": "NOT_AVAILABLE", "reason": "No validated real-data model installed. True/false alarm predictions deliberately disabled."})


def inject_fault(original: RecordCreate, fault: FaultRequest) -> RecordCreate:
    rng = np.random.default_rng(42)
    channels = []
    present = {c.name for c in original.channels}
    if fault.target not in present:
        raise ValueError("Selected channel not present")
    for channel in original.channels:
        data = list(channel.samples)
        if channel.name == fault.target:
            a = np.array([float('nan') if x is None else x for x in data], dtype=float)
            valid = np.isfinite(a)
            if not valid.any():
                raise ValueError("Cannot inject into an entirely missing signal")
            span = float(np.ptp(a[valid]))
            amplitude = max(span, float(np.std(a[valid])), .01)
            t = np.arange(len(a))/original.sample_rate_hz
            if fault.kind == "dropout":
                n = max(1, int(len(a) * (0.06 + .18*fault.severity)))
                start = (len(a)-n)//2
                a[start:start+n] = np.nan
            elif fault.kind == "baseline_drift":
                a[valid] += fault.severity * amplitude * np.sin(2*np.pi*0.17*t[valid])
            elif fault.kind == "mains_interference":
                a[valid] += fault.severity * amplitude * .75 * np.sin(2*np.pi*50*t[valid])
            elif fault.kind == "clipping":
                med = float(np.median(a[valid]))
                bound = max(amplitude * (0.4-0.28*fault.severity), 1e-5)
                a[valid] = np.clip(a[valid], med-bound, med+bound)
            data = [None if not np.isfinite(v) else float(v) for v in a]
        channels.append(Channel(kind=channel.kind, name=channel.name, unit=channel.unit, samples=data))
    return RecordCreate(title=original.title+" · "+fault.kind.replace('_',' '),
                        sample_rate_hz=original.sample_rate_hz, channels=channels,
                        origin=original.origin,
                        source_reference=original.source_reference + " | DERIVED FAULT EXPERIMENT: source annotation does not transfer",
                        reference_label="Unlabeled")


def preview(record: RecordCreate, max_points: int = 1400, start_s: float = 0, window_s: float | None = None) -> list[dict]:
    """Use ECG peak-preserving decimation with a common time grid for aligned traces."""
    total = len(record.channels[0].samples)
    fs = record.sample_rate_hz
    first = min(total-1, max(0, int(round(start_s * fs))))
    last = total if window_s is None else min(total, first + max(1, int(round(window_s * fs))))
    span = last-first
    if span <= max_points:
        indices = np.arange(first, last, dtype=int)
    else:
        count = max(1, max_points // 2)
        bounds = np.linspace(first, last, count+1, dtype=int)
        # Use ECG as representative; all channels share these timestamps for synchronization.
        reference = next((c for c in record.channels if c.kind == 'ECG'), record.channels[0])
        values = np.array([np.nan if x is None else float(x) for x in reference.samples[first:last]])
        picks = []
        for a,b in zip(bounds[:-1],bounds[1:]):
            chunk = values[a-first:b-first]
            finite = np.flatnonzero(np.isfinite(chunk))
            if finite.size:
                lo = a+int(finite[np.argmin(chunk[finite])])
                hi = a+int(finite[np.argmax(chunk[finite])])
                picks.extend(sorted({lo,hi}))
            else:
                picks.append(a)
        indices = np.array(sorted(set(picks)), dtype=int)
    return [{"kind":c.kind, "name":c.name, "unit":c.unit,
             "t":[round(int(i)/fs,4) for i in indices],
             "values":[c.samples[int(i)] for i in indices]} for c in record.channels]


def demo_record(kind: str) -> RecordCreate:
    if kind not in {"baseline", "tachy_simulation", "artifact"}:
        raise ValueError("Unknown demo")
    fs = 250
    t = np.arange(0, 12, 1/fs)
    bpm = 145 if kind == 'tachy_simulation' else 72
    phase = np.mod(t*bpm/60., 1.0)
    def gaussian(mu, sigma, amp):
        p = np.minimum(np.abs(phase-mu), 1-np.abs(phase-mu))
        return amp*np.exp(-.5*(p/sigma)**2)
    ecg = (gaussian(.2, .035, .12)+gaussian(.49,.012,-.23)+gaussian(.51,.009,1.25)+
           gaussian(.54,.017,-.31)+gaussian(.76,.06,.25)+.015*np.sin(2*np.pi*.2*t))
    ppg = 0.55 + 0.6*np.exp(-.5*((phase-.76)/.11)**2) + .015*np.sin(2*np.pi*.1*t)
    abp = 79 + 37*np.exp(-.5*((phase-.73)/.15)**2)
    if kind == 'artifact':
        ecg += .7*np.sin(2*np.pi*50*t)
    return RecordCreate(title={"baseline":"Synthetic baseline · 72 BPM", "tachy_simulation":"Synthetic fast rhythm · 145 BPM", "artifact":"Synthetic mains interference"}[kind],
        sample_rate_hz=fs, origin="synthetic", source_reference="WaveAssure deterministic educational simulator seed=42",
        channels=[Channel(kind="ECG",unit="mV",samples=ecg.tolist()),
                  Channel(kind="PPG",unit="a.u.",samples=ppg.tolist()),
                  Channel(kind="ABP",unit="mmHg",samples=abp.tolist())])
