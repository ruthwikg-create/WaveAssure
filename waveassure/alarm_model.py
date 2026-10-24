"""Offline-only research VT-alarm feature extraction and JSON model inference.

Features describe the 30-second interval immediately *before* annotated alarm onset.
No trained model ships with WaveAssure. NOT FOR CLINICAL USE.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import base64
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfiltfilt, find_peaks

MODEL_SCHEMA = 'waveassure-vt-logistic-v1'
ALARM_SECOND = 300
FEATURE_SECONDS = 30
FEATURE_NAMES = [
    f'{lead}_{metric}' for lead in ('ecg1', 'ecg2')
    for metric in ('missing_fraction', 'std', 'iqr', 'difference_median', 'peak_rate', 'rr_cv')
] + ['pleth_missing_fraction', 'pleth_std', 'pleth_iqr', 'pleth_peak_rate']
KNOWN_ECG = {'I','II','III','AVR','AVL','AVF','V','V1','V2','V3','V4','V5','V6','MLII'}


def _window(data: np.ndarray, fs: float, alarm_s: float = ALARM_SECOND) -> np.ndarray:
    if data.ndim != 2 or data.shape[0] < 1:
        raise ValueError('Expected a nonempty 2D waveform')
    if not 50 <= fs <= 1000 or not math.isfinite(fs):
        raise ValueError('Unsupported sampling frequency')
    end = int(round(alarm_s * fs))
    start = end - int(round(FEATURE_SECONDS * fs))
    if start < 0 or end > len(data):
        raise ValueError('At least 300 seconds of waveform required: no post-alarm data used')
    return np.asarray(data[start:end], dtype=np.float64)


def _stats(x: np.ndarray, fs: float, is_ecg: bool) -> list[float]:
    finite = np.isfinite(x)
    missing = 1.0 - np.mean(finite)
    if finite.sum() < int(5 * fs):
        return [float(missing), *([float('nan')] * (5 if is_ecg else 3))]
    good_x = np.interp(np.arange(len(x)), np.flatnonzero(finite), x[finite]); good_x -= np.median(good_x)
    std = float(np.std(good_x))
    iqr = float(np.quantile(good_x, .75) - np.quantile(good_x, .25))
    # Baseline filtering is only for feature generation, not arrhythmia identification.
    try:
        low, high = (2.0, min(35.0, .4*fs)) if is_ecg else (.5, min(5.0, .4*fs))
        filtered = sosfiltfilt(butter(2, [low, high], btype='bandpass', fs=fs, output='sos'), good_x)
        # Use both polarities to avoid losing inverted ECG leads.
        prominence = max(float(np.std(filtered))*.9, float(np.ptp(filtered))*.22, 1e-10)
        distance = max(1, int(fs*(.28 if is_ecg else .35)))
        positive, _ = find_peaks(filtered, distance=distance, prominence=prominence)
        negative, _ = find_peaks(-filtered, distance=distance, prominence=prominence)
        peaks = positive if len(positive) >= len(negative) else negative
        intervals = np.diff(peaks)/fs
        rate = float(60 / np.median(intervals)) if len(intervals) >= 2 else float('nan')
        rr_cv = float(np.std(intervals)/np.mean(intervals)) if len(intervals) >= 2 and np.mean(intervals)>0 else float('nan')
    except ValueError:
        rate, rr_cv = float('nan'), float('nan')
    if is_ecg:
        return [float(missing), std, iqr, float(np.median(np.abs(np.diff(good_x)))), rate, rr_cv]
    return [float(missing), std, iqr, rate]


def extract_features(data: np.ndarray, names: list[str], fs: float, alarm_s: float = ALARM_SECOND) -> list[float]:
    if data.ndim != 2 or data.shape[1] != len(names):
        raise ValueError('Channel name count does not match waveform columns')
    window = _window(data, fs, alarm_s)
    ecg = [i for i, name in enumerate(names) if name.upper().startswith('ECG') or name.upper() in KNOWN_ECG]
    if not ecg:
        raise ValueError('ECG leads missing: VT feature extractor requires ECG')
    pleth = next((i for i, name in enumerate(names) if name.upper() in {'PLETH','PPG'}), None)
    feature_values = []
    for i in range(2):
        feature_values.extend(_stats(window[:,ecg[i]], fs, True) if i < len(ecg) else [float('nan')]*6)
    feature_values.extend(_stats(window[:,pleth], fs, False) if pleth is not None else [float('nan')]*4)
    if len(feature_values) != len(FEATURE_NAMES):
        raise AssertionError('Feature schema mismatch')
    return feature_values


def features_from_record(record) -> list[float]:
    """Inference parity with the local WaveAssure importer, no label as a feature."""
    data = np.column_stack([[np.nan if x is None else x for x in ch.samples] for ch in record.channels])
    return extract_features(data, [ch.name for ch in record.channels], float(record.sample_rate_hz))


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def export_model(model, medians, means, scales, provenance: dict, path: Path):
    """Store plain JSON, not unsafe Python pickle/joblib deserialization."""
    artifact = {'schema':MODEL_SCHEMA, 'feature_names':FEATURE_NAMES, 'median':np.asarray(medians).tolist(),
                'mean':np.asarray(means).tolist(), 'scale':np.asarray(scales).tolist(),
                'coefficients':model.coef_[0].tolist(), 'intercept':float(model.intercept_[0]),
                'threshold':float(provenance['threshold']), 'provenance':provenance}
    digest = hashlib.sha256(_canonical(artifact)).hexdigest()
    artifact['sha256'] = digest
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, allow_nan=False), encoding='utf-8')
    return artifact


def verify_model_attestation(path: Path, digest: str, trusted_key_path: Path | None = None) -> dict:
    """Verify an installation-pinned Ed25519 signature, not a self-declared checksum.

    This attests to release custody only. It NEVER establishes clinical validity.
    Signing keys and attestation files are not included in the distribution.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    import binascii

    trusted = trusted_key_path or os.environ.get('WAVEASSURE_TRUSTED_RESEARCH_KEY')
    if not trusted:
        raise ValueError('No external trusted model verification key configured; inference disabled')
    key_path = Path(trusted)
    if not key_path.is_file():
        raise ValueError('Trusted verifier key file missing')
    if key_path.stat().st_size != 32:
        raise ValueError('Expected raw 32-byte Ed25519 public verification key')
    sidecar = path.with_suffix('.attestation.json')
    if not sidecar.is_file() or sidecar.stat().st_size > 8192:
        raise ValueError('Independent model attestation file is missing or invalid')
    try:
        att = json.loads(sidecar.read_text(encoding='utf-8'))
        if (att.get('schema') != 'waveassure-model-attestation-v1'
            or att.get('model_sha256') != digest
            or att.get('scope') != 'research_integrity_only'
            or set(att) != {'schema', 'model_sha256', 'scope', 'signer_id', 'signature_base64'}
            or not isinstance(att['signer_id'], str) or not (1 <= len(att['signer_id']) <= 100)):
            raise ValueError('Model attestation metadata invalid or mismatched')
        signature = base64.b64decode(att['signature_base64'], validate=True)
        message = b'waveassure-model-attestation-v1\n' + _canonical({k:att[k] for k in ('schema','model_sha256','scope','signer_id')})
        Ed25519PublicKey.from_public_bytes(key_path.read_bytes()).verify(signature, message)
    except (ValueError, KeyError, TypeError, InvalidSignature, binascii.Error) as exc:
        raise ValueError('Untrusted model attestation: signature or metadata invalid') from exc
    return {'signer_id':att['signer_id'], 'scope':att['scope'], 'signature_verified':True,
            'clinical_validation':False}

def read_model(path: Path, *, internal_smoke_test: bool=False, trusted_key_path: Path | None=None):
    if not path.is_file():
        raise FileNotFoundError('No trained retrospective research model is installed')
    if path.stat().st_size > 100_000:
        raise ValueError('Unexpected model file size')
    model = json.loads(path.read_text(encoding='utf-8'))
    checksum = model.pop('sha256', None)
    computed = hashlib.sha256(_canonical(model)).hexdigest()
    if checksum != computed:
        raise ValueError('Research model checksum mismatch')
    model['sha256'] = checksum
    if not isinstance(model.get('provenance'),dict):
        raise ValueError('Research model provenance missing or invalid')
    if not internal_smoke_test and model.get('provenance',{}).get('training_mode','').startswith('ARTIFICIAL SMOKE TEST'):
        raise ValueError('Engineering smoke-test models may not be installed for application inference')
    if model.get('schema') != MODEL_SCHEMA or model.get('feature_names') != FEATURE_NAMES:
        raise ValueError('Unsupported model or feature schema')
    for name in ('median', 'mean', 'scale', 'coefficients'):
        arr = np.asarray(model[name], dtype=float)
        if arr.shape != (len(FEATURE_NAMES),) or not np.isfinite(arr).all():
            raise ValueError(f'Invalid model parameters: {name}')
    if not math.isfinite(float(model['intercept'])) or any(s <= 0 for s in model['scale']):
        raise ValueError('Invalid logistic regression model scales/intercept')
    if not 0 < float(model['threshold']) < 1:
        raise ValueError('Invalid model threshold')
    if not internal_smoke_test:
        model['attestation'] = verify_model_attestation(path, checksum, trusted_key_path)
    return model


def assess(model: dict, features: list[float], *, enforce_signal_quality: bool=False) -> dict:
    x = np.asarray(features, dtype=float).copy()
    if x.shape != (len(FEATURE_NAMES),):
        raise ValueError('Feature schema mismatch')
    missing = ~np.isfinite(x)
    # Fail safe on missing lead-1 evidence or excessive missingness. No model
    # score is presented if the input quality is outside this explicit scope.
    if enforce_signal_quality and (missing[:6].any() or not (0 <= x[0] <= 0.20)):
        raise ValueError('ABSTAIN: primary ECG evidence unavailable or has over 20% missing samples')
    if enforce_signal_quality and missing.sum() > 8:
        raise ValueError('ABSTAIN: too many unavailable waveform features')
    x[missing] = np.asarray(model['median'])[missing]
    x = (x - np.asarray(model['mean']))/np.asarray(model['scale'])
    z = float(np.clip(x @ np.asarray(model['coefficients']) + model['intercept'], -80, 80))
    probability = float(1 / (1 + np.exp(-z)))
    return {'research_probability_true_vt':round(probability, 6),
            'threshold':model['threshold'],
            'exploratory_classification':'True VT candidate' if probability >= model['threshold'] else 'False VT candidate',
            'missing_feature_count':int(missing.sum()),
            'model_sha256':model['sha256'],
            'limitations':'RETROSPECTIVE RESEARCH ONLY. This is NOT a verified clinical probability. Never suppress or prioritize patient alarms based on this value.'}
