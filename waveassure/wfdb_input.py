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


def decode_format16(header_name: str, header_bytes: bytes, data_name: str, data_bytes: bytes,
                    source_reference: str, title: str, reference_label: str = 'Unlabeled',
                    alarm_time_s: float | None = None, alarm_source: str | None = None) -> RecordCreate:
    """Validate a bounded WFDB format-16 pair entirely in memory; never execute headers."""
    base = header_name[:-4] if header_name.endswith('.hea') else ''
    if not re.fullmatch(r'[A-Za-z0-9_-]+', base) or data_name != base + '.dat':
        raise ValueError('Select matching WFDB .hea and .dat files with a safe common basename')
    if not header_bytes or len(header_bytes) > 8192 or len(data_bytes) > 1_600_000:
        raise ValueError('WFDB header or waveform exceeds bounded research limits')
    try:
        lines = [line.strip() for line in header_bytes.decode('ascii').splitlines()
                 if line.strip() and not line.startswith('#')]
        if not lines:
            raise ValueError('WFDB header contains no recording metadata')
        fields = lines[0].split()
        if len(fields) < 4 or fields[0] != base:
            raise ValueError('Malformed WFDB master header')
        n = int(fields[1]); fs = float(fields[2]); count = int(fields[3])
        if not (1 <= n <= 8 and 50 <= fs <= 1000 and 100 <= count <= 100_000 and count/fs <= 600):
            raise ValueError('Recording outside bounded study limits')
        if len(lines) < n+1:
            raise ValueError('Missing WFDB signal header lines')
        parsed = []
        for line in lines[1:n+1]:
            parts = line.split()
            if len(parts) < 9 or parts[0] != data_name or parts[1] != '16':
                raise ValueError('Unsupported WFDB layout: requires shared file and format 16')
            cal = ADC_RE.fullmatch(parts[2])
            if cal is None:
                raise ValueError('Missing or unsupported ADC calibration')
            gain = float(cal.group('gain'))
            baseline = int(cal.group('baseline') or parts[4])
            if gain <= 0 or not np.isfinite(gain):
                raise ValueError('Invalid ADC gain')
            name = parts[-1]
            kind = 'PPG' if name == 'PLETH' else 'ABP' if name == 'ABP' else 'ECG'
            unit = cal.group('unit')
            if kind == 'ECG' and (unit != 'mV' or name not in
                    {'II','I','III','aVR','aVL','aVF','V','V1','V2','V3','V4','V5','V6'}):
                raise ValueError('Unsupported ECG lead name or units')
            if kind == 'PPG' and unit != 'NU':
                raise ValueError('Unsupported plethysmography units')
            if kind == 'ABP' and unit != 'mmHg':
                raise ValueError('Unsupported arterial pressure units')
            parsed.append((kind,name,unit,gain,baseline,int(parts[6])))
        expected = count * n * 2
        if len(data_bytes) != expected:
            raise ValueError(f'Incomplete waveform: {len(data_bytes):,}/{expected:,} bytes')
        digital = np.frombuffer(data_bytes,dtype='<i2').reshape(count,n)
        channels=[]
        for index,(kind,name,unit,gain,baseline,checksum) in enumerate(parsed):
            observed = int(np.sum(digital[:,index],dtype=np.int64)) & 0xffff
            if observed != (checksum & 0xffff):
                raise ValueError(f'WFDB digital-sample checksum mismatch in {name}')
            physical = (digital[:,index].astype(np.float64)-baseline)/gain
            missing = digital[:,index] == -32768
            samples=[None if missing[i] else float(x) for i,x in enumerate(physical)]
            channels.append(Channel(kind=kind,name=name,unit=unit,samples=samples))
        return RecordCreate(title=title[:64],sample_rate_hz=fs,channels=channels,
                            origin='wfdb_research',source_reference=source_reference[:240],
                            reference_label=reference_label,alarm_time_s=alarm_time_s,
                            alarm_time_source=alarm_source)
    except (UnicodeError,IndexError,OverflowError,TypeError) as exc:
        raise ValueError('Unable to decode constrained WFDB format-16 recording') from exc


def import_local_wfdb(record_path: str) -> RecordCreate:
    path_text = record_path.replace('\\', '/')
    if not RECORD_PATTERN.fullmatch(path_text):
        raise ValueError('Use a relative WFDB basename, e.g. sample/623dd0/623dd0_0023 (without extension).')
    root = configured_root()
    if not root.is_dir():
        raise ValueError('WFDB dataset directory missing: configure WAVEASSURE_WFDB_ROOT')
    base = (root/path_text).resolve()
    if not base.is_relative_to(root):
        raise ValueError('WFDB record path escapes the configured dataset directory')
    hea,dat = base.with_suffix('.hea'),base.with_suffix('.dat')
    if not hea.is_file() or not dat.is_file():
        raise ValueError('Matching WFDB .hea and .dat files must exist')
    if hea.stat().st_size > 8192 or dat.stat().st_size > 1_600_000:
        raise ValueError('WFDB file exceeds bounded research size limits')
    reference = _reference_label(root,base.parent.name,base.name)
    # The VTaC dataset documents an alarm onset at 300 s. Apply this only when
    # its event_labels.csv matched the exact recording; never to arbitrary WFDB.
    annotated = reference in {'True', 'False'} and (root / 'event_labels.csv').is_file() and _header_duration_at_least_300(hea)
    return decode_format16(hea.name,hea.read_bytes(),dat.name,dat.read_bytes(),
                           source_reference=f'Local VTaC research record {path_text}; WFDB checksums verified; source authenticity unconfirmed',
                           title=('VTaC · '+base.name)[:64],reference_label=reference,
                           alarm_time_s=300.0 if annotated else None,
                           alarm_source='dataset_annotation' if annotated else None)


def _header_duration_at_least_300(hea: Path) -> bool:
    try:
        row=hea.read_text(encoding='ascii').splitlines()[0].split()
        return float(row[3])/float(row[2]) >= 300
    except (ValueError,IndexError,OSError,ZeroDivisionError):
        return False


def import_uploaded_wfdb(header_filename: str, header_text: str,
                         data_filename: str, data_bytes: bytes,
                         alarm_time_s: float | None = None) -> RecordCreate:
    # Browser uploads have no external reference labels; a user timestamp is a
    # documented unverified annotation and never enables the VT research model.
    return decode_format16(header_filename,header_text.encode('ascii'),data_filename,data_bytes,
                           source_reference='Local user-selected WFDB pair: format/checksum only; no expert label or source authentication',
                           title='Custom WFDB · '+header_filename[:-4],
                           alarm_time_s=alarm_time_s,
                           alarm_source='user_annotation_unverified' if alarm_time_s is not None else None)
