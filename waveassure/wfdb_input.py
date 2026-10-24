"""Constrained offline WFDB reader for simple multichannel format-16 research records.

Protects against incomplete files and mislabelled/uncalibrated signals.
Not a general WFDB decoder or verified patient monitor interface.
"""
from __future__ import annotations
import csv
import os
import re
from pathlib import Path
import numpy as np
from .schemas import Channel, RecordCreate

RECORD_PATTERN = re.compile(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*\Z")
ADC_RE = re.compile(r"^(?P<gain>[0-9]+(?:\.[0-9]+)?)(?:\((?P<baseline>-?[0-9]+)\))?/(?P<unit>[A-Za-z0-9.]+)$")


def configured_root() -> Path:
    return Path(os.environ.get('WAVEASSURE_WFDB_ROOT', r'D:\WaveAssure-Datasets')).resolve()


def _reference_label(root: Path, record_id: str, event: str) -> str:
    labels = root / 'event_labels.csv'
    if not labels.is_file():
        return 'Unlabeled'
    try:
        with labels.open('r', encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                if row.get('record') == record_id and row.get('event') == event:
                    value = str(row.get('decision', '')).strip()
                    return value if value in {'True', 'False'} else 'Unlabeled'
    except (OSError, UnicodeError, csv.Error):
        return 'Unlabeled'
    return 'Unlabeled'


def import_local_wfdb(record_path: str) -> RecordCreate:
    # API accepts a RELATIVE RECORD BASE path, not an arbitrary filesystem path.
    path_text = record_path.replace('\\', '/')
    if not RECORD_PATTERN.fullmatch(path_text):
        raise ValueError('Use a relative waveform basename, e.g. sample/623dd0/623dd0_0023 (no extension).')
    root = configured_root()
    if not root.is_dir():
        raise ValueError('WFDB dataset directory missing: set WAVEASSURE_WFDB_ROOT before launching.')
    base = (root / path_text).resolve()
    if not base.is_relative_to(root):
        raise ValueError('File path is outside the configured research dataset directory')
    hea = base.with_suffix('.hea')
    if not hea.is_file() or hea.stat().st_size > 8192:
        raise ValueError('WFDB header missing or unexpectedly large')
    try:
        header_lines = [line.strip() for line in hea.read_text(encoding='ascii').splitlines() if line.strip() and not line.startswith('#')]
        if not header_lines:
            raise ValueError('WFDB header contains no recording metadata')
        record_fields = header_lines[0].split()
        if len(record_fields) < 4 or record_fields[0] != base.name:
            raise ValueError('Malformed WFDB master header')
        nch = int(record_fields[1]); fs = float(record_fields[2]); nsamp = int(record_fields[3])
        if not (1 <= nch <= 8 and 50 <= fs <= 1000 and 100 <= nsamp <= 100_000 and nsamp / fs <= 600):
            raise ValueError('Recording outside bounded study limits')
        if len(header_lines) < nch+1:
            raise ValueError('Missing WFDB signal header lines')
        parsed = []
        data_name = base.name + '.dat'
        for line in header_lines[1:nch+1]:
            parts = line.split()
            if len(parts) < 9 or parts[0] != data_name or parts[1] != '16':
                raise ValueError('Unsupported WFDB layout (only shared-file, format 16)')
            calibration = ADC_RE.fullmatch(parts[2])
            if not calibration:
                raise ValueError('Missing or unsupported ADC calibration')
            gain = float(calibration.group('gain'))
            baseline = int(calibration.group('baseline') or parts[4])
            if gain <= 0 or not np.isfinite(gain):
                raise ValueError('Invalid ADC gain')
            kind = 'PPG' if parts[-1] == 'PLETH' else 'ABP' if parts[-1] == 'ABP' else 'ECG'
            unit = calibration.group('unit')
            if kind == 'ECG' and (unit != 'mV' or parts[-1] not in {'II','I','III','aVR','aVL','aVF','V','V1','V2','V3','V4','V5','V6'}):
                raise ValueError('Unsupported ECG lead name or units')
            if kind == 'PPG' and unit != 'NU':
                raise ValueError('Unsupported plethysmography units')
            if kind == 'ABP' and unit != 'mmHg':
                raise ValueError('Unsupported arterial-pressure units')
            parsed.append((kind, parts[-1], unit, gain, baseline, int(parts[6])))
        dat = base.with_suffix('.dat')
        if not dat.is_file():
            raise ValueError('Matching WFDB .dat file is missing')
        expected_bytes = nsamp*nch*2
        if dat.stat().st_size != expected_bytes:
            raise ValueError(f'Incomplete waveform: {dat.stat().st_size:,}/{expected_bytes:,} bytes')
        digital = np.fromfile(dat, dtype='<i2')
        if digital.size != nsamp*nch:
            raise ValueError('Signal length differs from WFDB header')
        digital = digital.reshape(nsamp,nch)
        channels = []
        for index,(kind,name,unit,gain,baseline,checksum) in enumerate(parsed):
            actual = int(np.sum(digital[:,index], dtype=np.int64)) & 0xFFFF
            if actual != (checksum & 0xFFFF):
                raise ValueError(f'WFDB digital-sample checksum mismatch in {name}')
            physical = (digital[:,index].astype(np.float64)-baseline)/gain
            missing = digital[:,index] == -32768  # WFDB format-16 invalid-sample marker
            samples = [None if missing[i] else float(x) for i,x in enumerate(physical)]
            channels.append(Channel(kind=kind,name=name,unit=unit,samples=samples))
        reference = _reference_label(root, base.parent.name, base.name)
        return RecordCreate(title='VTaC · '+base.name, sample_rate_hz=fs,
                channels=channels, origin='wfdb_research',
                source_reference=f'VTaC local research record {base.parent.name}/{base.name}; sample checksums verified; data origin not authenticated by this loader',
                reference_label=reference)
    except (OSError,UnicodeError,IndexError,OverflowError,TypeError) as exc:
        raise ValueError('Unable to decode constrained WFDB format-16 recording') from exc
