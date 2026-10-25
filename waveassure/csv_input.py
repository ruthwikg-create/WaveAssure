"""Bounded, user-mapped CSV research import; no clinical or patient identity verification."""
import csv
import io
import math
import re
from .schemas import CSVImport, Channel, RecordCreate, CSVChannelMap

CHANNEL_HEADERS = {'ECG_mV': ('ECG', 'mV'), 'PPG_au': ('PPG', 'a.u.'), 'ABP_mmHg': ('ABP', 'mmHg')}
SENSITIVE_WORDS = {'patient', 'subject', 'name', 'first_name', 'last_name', 'dob',
                   'birth', 'email', 'phone', 'address', 'mrn', 'medical_record', 'person_id'}


# These are metadata/summary labels, not recorded waveform sample columns.
# Enforce this in the server even when the browser is bypassed.
NON_WAVEFORM_TOKENS = {'alert', 'alarm', 'flag', 'status', 'accuracy',
                       'diagnosis', 'diagnostic', 'risk', 'classification',
                       'label', 'warning'}
SCALAR_MEASUREMENT_HEADERS = {'heart_rate', 'heartrate', 'pulse_rate',
                              'spo2', 'oxygen_saturation', 'respiration_rate',
                              'respiratory_rate', 'body_temperature', 'temperature'}


def is_non_waveform_column(header: str) -> bool:
    normalized = re.sub(r'[^a-z0-9]+', '_', header.strip().lower()).strip('_')
    return normalized in SCALAR_MEASUREMENT_HEADERS or bool(
        set(normalized.split('_')) & NON_WAVEFORM_TOKENS)


def parse_csv(data: CSVImport) -> RecordCreate:
    reader = csv.DictReader(io.StringIO(data.csv_text.lstrip('\ufeff'), newline=''))
    headers = reader.fieldnames
    if not headers or len(set(headers)) != len(headers) or any(not h for h in headers):
        raise ValueError('CSV needs unique, nonempty column headers')
    lowered = [h.lower().replace(' ', '_') for h in headers]
    if any(any(token in h for token in SENSITIVE_WORDS) for h in lowered):
        raise ValueError('Identifying column headers are not allowed (such as Patient Number). Remove identifiers from the source CSV before import. Patient-level alert tables are not waveform recordings.')
    explicit = data.channel_mapping is not None
    if explicit:
        if len(data.channel_mapping) < 1 or len(data.channel_mapping) > 8:
            raise ValueError('Select between 1 and 8 waveform columns')
        chosen = data.channel_mapping
    else:
        # Backward-compatible strict import when the user has not mapped columns.
        extra = set(headers) - {'time_s', *CHANNEL_HEADERS}
        if extra:
            raise ValueError('Unsupported columns (including identifiers) forbidden: ' + ', '.join(sorted(extra)))
        chosen = [CSVChannelMap(column=h, kind=CHANNEL_HEADERS[h][0], unit=CHANNEL_HEADERS[h][1], name=CHANNEL_HEADERS[h][0])
                  for h in CHANNEL_HEADERS if h in headers]
    disallowed = [c.column for c in chosen if is_non_waveform_column(c.column)]
    if disallowed:
        raise ValueError('Alert, quality and scalar vital-sign columns cannot be mapped as waveform samples: ' + ', '.join(disallowed) + '. Import recorded ECG/PPG/ABP waveform samples with elapsed time, not patient summary or alert tables.')
    if data.time_column not in headers:
        raise ValueError('Selected time column is missing')
    if not chosen:
        raise ValueError('Select at least one signal column')
    if any(c.column not in headers or c.column == data.time_column for c in chosen):
        raise ValueError('Selected signal column missing or is the time column')
    if len({c.column for c in chosen}) != len(chosen) or len({c.name for c in chosen}) != len(chosen):
        raise ValueError('Signal columns and names must each be unique')
    times = []
    columns = {c.column: [] for c in chosen}
    for row in reader:
        if len(times) >= 100_000:
            raise ValueError('CSV maximum is 100000 samples')
        if None in row:
            raise ValueError('CSV row has extra fields')
        try:
            t = float(row[data.time_column]) / (1000 if data.time_unit == 'ms' else 1)
            if not math.isfinite(t):
                raise ValueError('Nonfinite time')
            times.append(t)
            for c in chosen:
                raw = row[c.column]
                sample = None if raw is None or not raw.strip() else float(raw)
                if sample is not None and not math.isfinite(sample):
                    raise ValueError('Nonfinite sample')
                columns[c.column].append(sample)
        except (TypeError, ValueError) as exc:
            raise ValueError(f'Invalid numeric value at sample {len(times)}') from exc
    if len(times) < 100:
        raise ValueError('At least 100 samples required')
    dt = [b-a for a,b in zip(times,times[1:])]
    if any(x <= 0 for x in dt):
        raise ValueError('Time must increase strictly')
    mid = sorted(dt)[len(dt)//2]
    if any(abs(x-mid) > mid*0.02 for x in dt):
        raise ValueError('Sampling intervals must be uniform within 2%')
    if abs(times[0]) > max(0.02,mid*2):
        raise ValueError('Time must start near 0 seconds; trim and rebase the CSV first')
    channels = [Channel(kind=c.kind, name=c.name, unit=c.unit, samples=columns[c.column]) for c in chosen]
    return RecordCreate(title=data.title, sample_rate_hz=1/mid, channels=channels,
                        origin='local_csv_unverified',
                        source_reference='User-mapped local CSV; waveform units and de-identification not independently verified',
                        alarm_time_s=data.alarm_time_s,
                        alarm_time_source='user_annotation_unverified' if data.alarm_time_s is not None else None)
