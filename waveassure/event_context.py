"""Bounded retrospective signal descriptions around a selected timestamp.

No independent ECG morphology diagnosis, vital-sign thresholds, alarm cause
inference, patient-safety assertion or source authenticity claim.
"""
from __future__ import annotations

import math
from .evidence import window_statistics
from .schemas import RecordCreate


def describe_at(record: RecordCreate, metadata: dict, at_s: float, radius_s: float = 2.0) -> dict:
    """Summarize original samples in a clipped ±radius_s window.

    A caller-selected timestamp is NOT proof that an alarm existed there.
    The originating waveform sample units may be unverified.
    """
    duration = len(record.channels[0].samples) / record.sample_rate_hz
    if not math.isfinite(at_s) or at_s < 0 or at_s > duration:
        raise ValueError("Inspection timestamp is outside this recording")
    if not math.isfinite(radius_s) or not (0.1 <= radius_s <= 5.0):
        raise ValueError("Inspection radius must be between 0.1 and 5 seconds")
    start = max(0.0, at_s - radius_s)
    end = min(duration, at_s + radius_s)
    stats = window_statistics(record, start, end)

    original = metadata.get('parent_id') is None
    source_time = record.alarm_time_s if original else None
    legacy_vtac = (original and record.origin == 'wfdb_research'
                   and record.reference_label in ('True', 'False')
                   and 'VTaC' in record.source_reference and duration >= 300)
    if source_time is None and legacy_vtac:
        source_time = 300.0
    aligns_with_event = source_time is not None and abs(source_time-at_s) <= 1/record.sample_rate_hz
    is_annotated_vt = (aligns_with_event and record.origin == 'wfdb_research'
                       and record.reference_label in ('True', 'False')
                       and (record.alarm_time_source == 'dataset_annotation' or legacy_vtac))
    if is_annotated_vt:
        reference = 'genuine_vt_alarm' if record.reference_label == 'True' else 'false_vt_alarm'
        source = 'Original WFDB VTaC research annotation; source authenticity not independently established'
    elif aligns_with_event and record.alarm_time_source == 'user_annotation_unverified':
        reference = 'unverified_user_time_cause_unknown'
        source = 'User-supplied event timestamp; no independently verified cause'
    else:
        reference = 'no_supported_event_reference'
        source = 'A selected time is not an alarm occurrence'
    for channel in stats['channels']:
        if channel['valid_samples'] == 0:
            observation = 'No finite samples in selected interval'
        elif channel['missing_samples']:
            observation = 'Missing samples present; review signal completeness'
        else:
            observation = 'Observed waveform values only; clinical normal/high/low not assessed'
        channel['technical_observation'] = observation
        channel['physiological_status'] = 'NOT_ASSESSED'
        channel['ecg_morphology'] = 'NOT_CLASSIFIED' if channel['kind'] == 'ECG' else 'NOT_APPLICABLE'
    return {
        'time_s': round(at_s, 6),
        'window_start_s': stats['start_s'],
        'window_end_s': stats['end_s'],
        'sample_interval': stats['interval'],
        'reference_event': reference,
        'reference_description': source,
        'reference_rhythm_category': (
            'VT (ventricular tachycardia) is the source ALARM category, not an independently diagnosed ECG morphology'
            if is_annotated_vt else None
        ),
        'channels': stats['channels'],
        'interpretation': 'Descriptive raw-sample statistics; not ECG rhythm classification or normal/high/low vital-sign alarms.',
        'sampling_calibration_verified': False,
        'clinical_assessment': 'NOT_PERFORMED',
    }
