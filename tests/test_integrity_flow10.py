"""Adversarial regression and API flow tests using artificial fixtures only.

These tests do not validate medical performance or authorize clinical use.
"""
import gzip
import json
import sqlite3

import pytest
from waveassure import storage
from waveassure.schemas import RecordCreate, Channel


def _fixture_case(label='True'):
    return storage.save(RecordCreate(
        title='Synthetic research fixture', origin='wfdb_research',
        source_reference='UNIT TEST ONLY', sample_rate_hz=50,
        reference_label=label,
        channels=[Channel(kind='ECG',name='II',unit='mV',samples=[.2]*15000)]))


def test_tampered_audit_stops_new_mutations_and_rolls_back(client):
    original = client.post('/api/demo?kind=baseline').json()['id']
    with storage.connect() as db:
        db.execute("UPDATE audit SET event='forged' WHERE seq=1")
    assert client.get('/api/audit').json()['verification']['ok'] is False
    response = client.post('/api/demo?kind=baseline')
    assert response.status_code == 409, response.text
    assert 'integrity' in response.text.lower()
    assert len(client.get('/api/records').json()['items']) == 1
    assert client.post(f'/api/records/{original}/fault',json={
        'kind':'dropout','target':'ECG','severity':.5}).status_code == 409
    assert len(client.get('/api/records').json()['items']) == 1


def test_gzip_corruption_returns_controlled_409_on_all_evidence_routes(client):
    rid=client.post('/api/demo?kind=baseline').json()['id']
    with storage.connect() as db:
        db.execute('UPDATE records SET payload=? WHERE id=?',(b'not gzip data',rid))
    for path in (f'/api/records/{rid}',f'/api/records/{rid}/preview',
                 f'/api/records/{rid}/evidence',f'/api/records/{rid}/report',
                 f'/api/records/{rid}/report.html'):
        assert client.get(path).status_code==409, path


def test_inconsistent_record_metadata_returns_409(client):
    rid=client.post('/api/demo?kind=baseline').json()['id']
    with storage.connect() as db:
        db.execute('UPDATE records SET title=? WHERE id=?',('Fake title',rid))
    assert client.get(f'/api/records/{rid}').status_code==409


def test_reviewer_freezes_source_checksum_for_session(client):
    rid=_fixture_case()
    session=client.post('/api/pilot/sessions',json={'reviewer_code':'anonymous-1'})
    assert session.status_code==201,session.text
    sid=session.json()['id']
    assert client.get(f'/api/pilot/sessions/{sid}/cases/{rid}').status_code==200
    # Administrator changes the stored case and recomputes matching checksum.
    # The recording is individually checksum-consistent but differs from the
    # record that the reviewer was originally assigned.
    result=storage.get(rid)
    result['record'].reference_label='False'
    raw=storage._canonical(result['record'].model_dump()).encode()
    import hashlib
    with storage.connect() as db:
        db.execute('UPDATE records SET payload=?,data_sha256=? WHERE id=?',
                   (gzip.compress(raw),hashlib.sha256(raw).hexdigest(),rid))
    assert client.get(f'/api/pilot/sessions/{sid}/cases/{rid}').status_code==422
    r=client.post(f'/api/pilot/sessions/{sid}/responses',json={
        'record_id':rid,'decision':'True','confidence':'low','quality':'limited'})
    assert r.status_code==422,r.text


def test_reviewer_freezes_source_before_export(client):
    rid=_fixture_case()
    sid=client.post('/api/pilot/sessions',json={'reviewer_code':'anonymous-1'}).json()['id']
    assert client.post(f'/api/pilot/sessions/{sid}/responses',json={
        'record_id':rid,'decision':'True','confidence':'low','quality':'limited'}).status_code==201
    assert client.post(f'/api/pilot/sessions/{sid}/finalize').status_code==200
    with storage.connect() as db:
        db.execute('UPDATE records SET data_sha256=? WHERE id=?',('0'*64,rid))
    assert client.get(f'/api/pilot/sessions/{sid}/export').status_code==409


def test_reviewer_create_session_rejects_corrupt_candidate(client):
    rid=_fixture_case()
    with storage.connect() as db:
        db.execute('UPDATE records SET payload=? WHERE id=?',(b'corrupt',rid))
    resp=client.post('/api/pilot/sessions',json={'reviewer_code':'anonymous-1'})
    assert resp.status_code==422
    assert 'Import at least one intact' in resp.text


def test_reviewer_blocks_finalization_when_case_source_changes(client):
    rid=_fixture_case()
    sid=client.post('/api/pilot/sessions',json={'reviewer_code':'anonymous-1'}).json()['id']
    response=client.post(f'/api/pilot/sessions/{sid}/responses',json={
        'record_id':rid,'decision':'Indeterminate','confidence':'low','quality':'limited'})
    assert response.status_code==201
    with storage.connect() as db:
        db.execute('UPDATE records SET data_sha256=? WHERE id=?',('0'*64,rid))
    result=client.post(f'/api/pilot/sessions/{sid}/finalize')
    assert result.status_code in (409,422), result.text
    assert client.get(f'/api/pilot/sessions/{sid}').json()['completed'] is False
