"""Negative assurance cases. All test models and waveforms are synthetic fixtures.

Passing these tests DOES NOT establish patient-care safety, regulatory approval,
clinical accuracy, or a genuinely blinded human-subject study.
"""
import base64
import hashlib
import json
import sqlite3

import numpy as np
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from waveassure import storage
from waveassure.alarm_model import FEATURE_NAMES, MODEL_SCHEMA, read_model, assess, _canonical
from waveassure.schemas import RecordCreate, Channel


def fixture_model(tmp_path, mode='RETROSPECTIVE VTaC RESEARCH BASELINE'):
    body = {'schema': MODEL_SCHEMA, 'feature_names': FEATURE_NAMES,
            'median': [0.0]*len(FEATURE_NAMES),
            'mean': [0.0]*len(FEATURE_NAMES), 'scale': [1.0]*len(FEATURE_NAMES),
            'coefficients': [0.0]*len(FEATURE_NAMES), 'intercept': 0.0,
            'threshold': 0.5,
            'provenance': {'training_mode':mode,'research_only':True}}
    body['sha256'] = hashlib.sha256(_canonical(body)).hexdigest()
    path = tmp_path/'vt_model.json'
    path.write_text(json.dumps(body), encoding='utf-8')
    return path, body


def sign_model(path, model, pub_path, signer_id='EXTERNAL_TEST_SIGNER'):
    key = Ed25519PrivateKey.generate()
    pub_path.write_bytes(key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw))
    payload = {'schema':'waveassure-model-attestation-v1',
               'model_sha256':model['sha256'],
               'scope':'research_integrity_only',
               'signer_id':signer_id}
    message = b'waveassure-model-attestation-v1\n' + _canonical(payload)
    payload['signature_base64'] = base64.b64encode(key.sign(message)).decode()
    path.with_suffix('.attestation.json').write_text(json.dumps(payload), encoding='utf-8')


def test_forged_checksum_does_not_activate_model(tmp_path,monkeypatch):
    path, _ = fixture_model(tmp_path)
    monkeypatch.delenv('WAVEASSURE_TRUSTED_RESEARCH_KEY',raising=False)
    with pytest.raises(ValueError, match='No external trusted model verification key'):
        read_model(path)


def test_trusted_release_signature_verifies_then_detects_model_tamper(tmp_path):
    path, model = fixture_model(tmp_path)
    pub = tmp_path/'custodian_pubkey.raw'
    sign_model(path, model, pub)
    loaded = read_model(path, trusted_key_path=pub)
    assert loaded['attestation']['signature_verified'] is True
    assert loaded['attestation']['clinical_validation'] is False
    # Even after an attacker recomputes the checksum, the pinned external signature fails.
    model['intercept'] = 2.5
    updated = {k:v for k,v in model.items() if k!='sha256'}
    model['sha256'] = hashlib.sha256(_canonical(updated)).hexdigest()
    path.write_text(json.dumps(model), encoding='utf-8')
    with pytest.raises(ValueError,match='Untrusted model attestation'):
        read_model(path,trusted_key_path=pub)


def test_signer_identity_is_covered_by_signature(tmp_path):
    path, model = fixture_model(tmp_path)
    pub = tmp_path/'p.raw'
    sign_model(path,model,pub)
    att=path.with_suffix('.attestation.json')
    info=json.loads(att.read_text())
    info['signer_id']='FRAUDULENT_CLINICIAN'
    att.write_text(json.dumps(info))
    with pytest.raises(ValueError,match='Untrusted model attestation'):
        read_model(path,trusted_key_path=pub)


def test_untrusted_verifier_key_rejected(tmp_path):
    path,model=fixture_model(tmp_path)
    pub=tmp_path/'trusted.raw'
    sign_model(path,model,pub)
    another=tmp_path/'different.raw'
    another.write_bytes(Ed25519PrivateKey.generate().public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw))
    with pytest.raises(ValueError,match='Untrusted model attestation'):
        read_model(path,trusted_key_path=another)


def test_smoke_test_cannot_become_research_assessment_even_if_signed(tmp_path):
    path,model=fixture_model(tmp_path,mode='ARTIFICIAL SMOKE TEST - NOT VTaC PERFORMANCE')
    pub=tmp_path/'trusted.raw'
    sign_model(path,model,pub)
    with pytest.raises(ValueError,match='smoke-test models'):
        read_model(path,trusted_key_path=pub)


def test_abstains_when_primary_ecg_unusable():
    mod={
        'median':[0]*16,'mean':[0]*16,'scale':[1]*16,
        'coefficients':[0]*16,'intercept':0.,'threshold':0.5,'sha256':'test'}
    x=[0]*16
    x[0]=0.35
    with pytest.raises(ValueError,match='ABSTAIN'):
        assess(mod,x,enforce_signal_quality=True)
    x[0]=0.0;x[4]=float('nan')
    with pytest.raises(ValueError,match='ABSTAIN'):
        assess(mod,x,enforce_signal_quality=True)


def test_isolated_review_disallows_label_and_engineering_routes(client,monkeypatch):
    key='study-evaluation-secret-'+'z'*32
    monkeypatch.setenv('WAVEASSURE_WORKSPACE_MODE','review')
    monkeypatch.setenv('WAVEASSURE_REVIEW_KEY',key)
    n=15000
    rid=storage.save(RecordCreate(
        title='Synthetic fixture; no patients',origin='wfdb_research',
        sample_rate_hz=50,source_reference='synthetic test',reference_label='True',
        channels=[Channel(kind='ECG',name='II',unit='mV',samples=[0.5]*n)]))
    # A previously observed bypass is now forbidden even when requested directly.
    for route in (f'/api/records/{rid}',f'/api/records/{rid}/evidence',
                  f'/api/records/{rid}/preview','/api/records','/api/audit',
                  '/api/research-model/status','/api/import-wfdb', '/api/requirements'):
        assert client.get(route).status_code == 403, route
    assert client.get('/').status_code == 200
    assert 'Research review' in client.get('/').text
    assert client.post('/api/pilot/sessions',json={'reviewer_code':'reader-01'}).status_code==401
    h={'X-WaveAssure-Review-Key':key}
    create=client.post('/api/pilot/sessions',json={'reviewer_code':'reader-01'},headers=h)
    assert create.status_code==201, create.text
    sid=create.json()['id']
    case=client.get(f'/api/pilot/sessions/{sid}/cases/{rid}',headers=h)
    assert case.status_code==200, case.text
    assert 'reference_label' not in case.text or case.json()['reference_label_included'] is False
    assert client.get(f'/api/pilot/sessions/{sid}/export',headers=h).status_code==409
    # An incorrect access key also cannot retrieve the session or the waveform.
    assert client.get(f'/api/pilot/sessions/{sid}/cases/{rid}',headers={'X-WaveAssure-Review-Key':'wrong'}).status_code==401
    response=client.post(f'/api/pilot/sessions/{sid}/responses',headers=h,
                         json={'record_id':rid,'decision':'False','confidence':'low','quality':'limited'})
    assert response.status_code==201, response.text
    assert client.post(f'/api/pilot/sessions/{sid}/finalize',headers=h).status_code==200
    report=client.get(f'/api/pilot/sessions/{sid}/export',headers=h)
    assert report.status_code==200
    assert report.json()['counts']['FN']==1
    assert report.json()['clinical_validation'] is False


def test_review_mode_rejects_missing_key_configuration(client,monkeypatch):
    monkeypatch.setenv('WAVEASSURE_WORKSPACE_MODE','review')
    monkeypatch.delenv('WAVEASSURE_REVIEW_KEY',raising=False)
    assert client.post('/api/pilot/sessions',json={'reviewer_code':'reader-01'}).status_code==401


def test_unknown_mode_fails_closed(client,monkeypatch):
    monkeypatch.setenv('WAVEASSURE_WORKSPACE_MODE','hospital')
    assert client.get('/api/health').status_code==503


def test_tampered_record_api_does_not_return_unhandled_500(client):
    rid=client.post('/api/demo?kind=baseline').json()['id']
    with storage.connect() as db:
        db.execute('UPDATE records SET data_sha256=? WHERE id=?',('0'*64,rid))
        db.commit()
    for path in (f'/api/records/{rid}',f'/api/records/{rid}/preview',
                 f'/api/records/{rid}/report',f'/api/records/{rid}/report.html',
                 f'/api/records/{rid}/evidence'):
        response=client.get(path)
        assert response.status_code==409,(path,response.text)
    response=client.post(f'/api/records/{rid}/fault',json={'kind':'dropout','target':'ECG'})
    assert response.status_code != 500


def test_printable_report_stylesheet_allowed_by_csp(client):
    rid=client.post('/api/demo?kind=baseline').json()['id']
    r=client.get(f'/api/records/{rid}/report.html')
    assert r.status_code==200
    assert 'href="/static/report.css"' in r.text
    assert '<style>' not in r.text
    assert "style-src 'self'" in r.headers['Content-Security-Policy']
    css=client.get('/static/report.css')
    assert css.status_code==200
    assert '.critical' in css.text
