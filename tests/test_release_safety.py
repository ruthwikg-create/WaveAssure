"""Release safety boundaries; regression checks are not medical validation."""
import hashlib
import pytest
from fastapi.testclient import TestClient
from waveassure.api import app
from scripts.verify_dataset_sha256 import parse_manifest, verify


def test_security_headers_and_loopback_health(client):
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.headers['cache-control'] == 'no-store'
    assert r.headers['x-frame-options'] == 'DENY'
    assert 'frame-ancestors' in r.headers['content-security-policy']


def test_reject_public_peer_request():
    with TestClient(app, base_url='http://localhost:8000', client=('192.0.2.17', 8888)) as test:
        assert test.get('/api/health').status_code == 403


def test_reject_dns_rebinding_host(client):
    assert client.get('/api/health', headers={'Host': 'evil.example'}).status_code == 403
    assert client.get('/api/health', headers={'Host': '127.0.0.1.evil.com'}).status_code == 403
    assert client.get('/api/health', headers={'Host': '127.0.0.1:8000'}).status_code == 200


def test_reject_cross_site_origin(client):
    assert client.post('/api/demo?kind=baseline', headers={'Origin': 'https://other.example'}).status_code == 403
    assert client.post('/api/demo?kind=baseline', headers={'Origin': 'http://testserver'}).status_code == 201


def test_reject_oversized_content_length(client):
    r = client.post('/api/demo?kind=baseline', headers={'Content-Length': '10000001'})
    assert r.status_code == 413


def test_synthetic_data_cannot_claim_expert_label(client):
    payload = dict(title='Purported real patient', sample_rate_hz=250, origin='synthetic',
        reference_label='True', source_reference='Verified clinical ground truth',
        channels=[{'kind': 'ECG', 'name': 'II', 'unit': 'mV', 'samples': [0.0] * 100}])
    r = client.post('/api/records', json=payload)
    assert r.status_code == 201
    full = client.get('/api/records/' + r.json()['id']).json()
    assert full['reference_label'] == 'Unlabeled'
    assert 'synthetic' in full['source_reference'].lower()


def test_dataset_sha256_partial_and_mismatch(tmp_path):
    (tmp_path/'waveforms').mkdir()
    a = tmp_path/'waveforms'/'a.dat'
    a.write_bytes(b'only_test_data')
    good = hashlib.sha256(a.read_bytes()).hexdigest()
    bad = '0' * 64
    manifest = tmp_path/'SHA256SUMS.txt'
    manifest.write_text(f'{good}  waveforms/a.dat\n{bad}  waveforms/missing.dat\n')
    result = verify(tmp_path, manifest)
    assert result['matching'] == 1
    assert result['missing'] == 1
    assert result['complete_manifest'] is False
    assert result['ok_for_checked_files'] is True
    a.write_bytes(b'altered')
    assert verify(tmp_path, manifest)['mismatching'] == 1


def test_dataset_sha256_reject_traversal(tmp_path):
    m = tmp_path/'SHA256SUMS.txt'
    m.write_text('0' * 64 + '  ../private.dat\n')
    with pytest.raises(ValueError, match='Unsafe'):
        parse_manifest(m)
