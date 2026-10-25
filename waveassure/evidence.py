"""Traceable descriptive research evidence, not diagnostic decision support.

No classification or physiological threshold claims are produced here. The only
reference label is copied from a recorded dataset annotation, not inferred.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any
import numpy as np
from .schemas import RecordCreate

EVIDENCE_SCHEMA = 'waveassure-evidence-v1'
ALARM_T = 300.0
WINDOW_SECONDS = 30.0


def window_statistics(record: RecordCreate, start_s: float, end_s: float) -> dict[str, Any]:
    """Count raw missing samples and describe observed finite values, preserving units.

    No interpolation, peak detection, abnormality thresholds, or diagnostic claims.
    Both endpoints are defined in seconds; intervals are half-open [start,end).
    """
    fs = record.sample_rate_hz
    total = len(record.channels[0].samples)
    start = min(total, max(0, int(round(start_s * fs))))
    end = min(total, max(start, int(round(end_s * fs))))
    channels: list[dict[str, Any]] = []
    for ch in record.channels:
        segment = np.asarray([np.nan if s is None else float(s) for s in ch.samples[start:end]], dtype=float)
        finite = segment[np.isfinite(segment)]
        count = int(segment.size)
        valid = int(finite.size)
        def r(value: float) -> float:
            return round(float(value), 6)
        channels.append({
            'channel': ch.name, 'kind': ch.kind, 'unit': ch.unit,
            'total_samples': count, 'valid_samples': valid, 'missing_samples': count - valid,
            'missing_fraction': r((count-valid)/count) if count else None,
            'minimum': r(finite.min()) if valid else None,
            'maximum': r(finite.max()) if valid else None,
            'mean': r(finite.mean()) if valid else None,
            'standard_deviation': r(finite.std()) if valid else None,
            'median': r(np.median(finite)) if valid else None,
        })
    return {
        'start_s': r(start/fs), 'end_s': r(end/fs),
        'interval': '[start_s, end_s)', 'data_window_available': end > start,
        'channels': channels,
    }


def create_evidence(record: RecordCreate, metadata: dict[str, Any], audit_verification: dict[str, Any]) -> dict[str, Any]:
    is_original_wfdb = record.origin == 'wfdb_research' and metadata.get('parent_id') is None
    duration = len(record.channels[0].samples) / record.sample_rate_hz
    # Legacy original VTaC labelled recordings from older builds had no explicit time.
    legacy_event = (is_original_wfdb and record.alarm_time_s is None
                    and record.reference_label in ('True', 'False')
                    and 'VTaC' in record.source_reference and duration >= ALARM_T)
    event_t = record.alarm_time_s if record.alarm_time_s is not None else (ALARM_T if legacy_event else None)
    has_event = metadata.get('parent_id') is None and event_t is not None and event_t <= duration
    source = (record.alarm_time_source if record.alarm_time_s is not None else
              'legacy_vtac_dataset_label' if legacy_event else None)
    reference = record.reference_label if is_original_wfdb else 'Unlabeled'
    # Derived records never inherit the adjudicated source label.
    if metadata.get('parent_id') is not None:
        reference = 'Unlabeled'
    windows = {'entire_recording': window_statistics(record, 0, duration)}
    if has_event:
        windows['pre_alarm_30s'] = window_statistics(record, max(0, event_t-WINDOW_SECONDS), event_t)
        windows['post_alarm_30s'] = window_statistics(record, event_t, min(duration,event_t+WINDOW_SECONDS))
    return {
        'schema': EVIDENCE_SCHEMA,
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Offline retrospective biomedical signal quality documentation',
        'scope': 'RESEARCH_ONLY_NOT_FOR_CLINICAL_DECISIONS',
        'data_class': 'DERIVED_FAULT_EXPERIMENT' if metadata.get('parent_id') else ('SYNTHETIC' if record.origin == 'synthetic' else ('IMPORTED_WFDB_RESEARCH' if record.origin == 'wfdb_research' else 'UNVERIFIED_CSV')),
        'record': {
            'id': metadata['id'], 'title': metadata['title'], 'origin': record.origin,
            'source_reference': record.source_reference,
            'parent_id': metadata.get('parent_id'), 'fault': metadata.get('fault'),
            'sample_rate_hz': record.sample_rate_hz,
            'sample_count_per_channel': len(record.channels[0].samples),
            'duration_s': round(duration, 6),
            'channel_count': len(record.channels),
            'channels': [{'name': c.name, 'kind': c.kind, 'unit': c.unit} for c in record.channels],
            'payload_sha256': metadata['data_sha256'],
        },
        'reference_annotation': {
            'label': reference,
            'type': 'EXTERNAL_DATASET_REFERENCE' if reference in ('True','False') else 'NOT_AVAILABLE',
            'event_type': 'ventricular_tachycardia_alarm' if has_event and reference in ('True','False') else None,
            'event_time_s': event_t if has_event else None,
            'event_time_source': source if has_event else None,
            'annotation_scope': 'A timestamp annotation, not an original audio recording or a model prediction' if has_event else None,
            'independently_verified_by_waveassure': False,
        },
        'descriptive_measurements': windows,
        'measurement_method': {
            'algorithm': 'waveassure-window-statistics-v1',
            'missing_values': 'null only; no interpolation',
            'standard_deviation': 'population standard deviation (ddof=0)',
            'sample_intervals': 'rounded to nearest integer sample; [start, end)',
            'calibration': 'Units inherited from imported WFDB header or caller-supplied synthetic/CSV schema',
            'uncertainty': 'No propagated calibration uncertainty provided; outputs are descriptive sample statistics',
        },
        'integrity': {
            'record_payload_sha256': metadata['data_sha256'],
            'checked_on_read': True,
            'format_level_check_at_import': is_original_wfdb,
            'official_dataset_sha256_verified': False,
            'audit_chain_currently_valid': bool(audit_verification.get('ok')),
            'audit_log_is_digitally_signed': False,
        },
        'decision_support': {
            'clinical_alarm_assessment': 'NOT_PERFORMED',
            'independent_true_false_vt_model_assessment': 'NOT_INCLUDED_IN_THIS_REPORT',
            'clinical_interpretation': None,
            'patient_management_recommendation': None,
            'alarm_prioritization': None,
        },
        'limitations': [
            'Measurements are descriptive, not diagnostic: there are no validated physiological reference ranges.',
            'Dataset True/False is an existing annotation, not a WaveAssure prediction or definitive independent clinical adjudication.',
            'A matching imported WFDB digital-sample checksum is not proof of authenticated source or original PhysioNet SHA-256 integrity.',
            'Sampling, calibration, de-identification, and external sensor accuracy were not independently verified.',
            'No clinical trial, clinical validation, regulatory clearance, IEC 62304 certification or ISO 14971 conformance is claimed.',
            'Never use this report for clinical action, alarm suppression or patient care.',
        ],
    }
