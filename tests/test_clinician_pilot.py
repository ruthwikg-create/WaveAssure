"""The reviewer workflow is tested with ONLY synthetic test fixtures, not clinical records."""
import hashlib, json
import pytest
from waveassure import storage
from waveassure.schemas import RecordCreate, Channel


def make_case(label):
    n=15_000 # 300 seconds at 50 Hz, enough for pre-alarm view
    return storage.save(RecordCreate(title='Synthetic unit-test WFDB fixture',origin='wfdb_research',sample_rate_hz=50,
        reference_label=label,source_reference='TEST DATA - NOT PATIENT DATA',
        channels=[Channel(kind='ECG',name='II',unit='mV',samples=[0.1]*n),
                  Channel(kind='PPG',name='PLETH',unit='NU',samples=[0.3]*n)]))


def test_pilot_requires_real_wfdb_origin(client):
    client.post('/api/demo?kind=baseline')
    resp=client.post('/api/pilot/sessions',json={'reviewer_code':'reviewer-01'})
    assert resp.status_code==422


def test_reviewer_workflow_and_report(client):
    rid1=make_case('True');rid2=make_case('False')
    opened=client.post('/api/pilot/sessions',json={'reviewer_code':'reviewer-1'})
    assert opened.status_code==201,opened.text
    session=opened.json();sid=session['id'];assert session['total_cases']==2
    assert 'reference_label' not in json.dumps(session)
    review=client.get(f'/api/pilot/sessions/{sid}/cases/{rid1}')
    assert review.status_code==200,review.text
    assert 'reference_label":"True"' not in review.text
    assert review.json()['waveforms']
    assert max(review.json()['waveforms'][0]['t'])<=300
    assert client.get(f'/api/pilot/sessions/{sid}/export').status_code==409
    for rid,decision in [(rid1,'True'),(rid2,'False')]:
        r=client.post(f'/api/pilot/sessions/{sid}/responses',json={'record_id':rid,'decision':decision,
              'confidence':'low','quality':'limited','notes':'Research-only signal description'})
        assert r.status_code==201,r.text
        assert client.post(f'/api/pilot/sessions/{sid}/responses',json={'record_id':rid,'decision':decision,
              'confidence':'low','quality':'limited'}).status_code==422
    final=client.post(f'/api/pilot/sessions/{sid}/finalize');assert final.status_code==200
    assert final.json()['completed']
    report=client.get(f'/api/pilot/sessions/{sid}/export').json()
    assert report['counts']['TP']==1 and report['counts']['TN']==1
    assert report['clinical_validation'] is False
    assert report['descriptive_sensitivity'] is None
    assert report['descriptive_specificity'] is None
    digest=report.pop('report_sha256');assert hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':')).encode()).hexdigest()==digest
    assert client.post(f'/api/pilot/sessions/{sid}/responses',json={'record_id':rid1,'decision':'False','confidence':'high','quality':'adequate'}).status_code==422
    assert client.get('/api/audit').json()['verification']['ok']


def test_reject_identifiers_and_unrecognized_case(client):
    rid=make_case('True')
    sid=client.post('/api/pilot/sessions',json={'reviewer_code':'rev-test'}).json()['id']
    assert client.post('/api/pilot/sessions',json={'reviewer_code':'A B'}).status_code==422
    assert client.get(f'/api/pilot/sessions/{sid}/cases/123').status_code==422
    assert client.post(f'/api/pilot/sessions/{sid}/responses',json={'record_id':'a'*32,'decision':'True','confidence':'high','quality':'adequate'}).status_code==422
    assert client.post(f'/api/pilot/sessions/{sid}/responses',json={'record_id':rid,'decision':'True','confidence':'high','quality':'adequate','notes':'Email me at contact@example.com'}).status_code==422


def test_pilot_unlabelled_does_not_claim_accuracy(client):
    rid=make_case('Unlabeled')
    sid=client.post('/api/pilot/sessions',json={'reviewer_code':'rev-id-7'}).json()['id']
    client.post(f'/api/pilot/sessions/{sid}/responses',json={'record_id':rid,'decision':'Indeterminate','confidence':'low','quality':'uninterpretable'})
    client.post(f'/api/pilot/sessions/{sid}/finalize')
    report=client.get(f'/api/pilot/sessions/{sid}/export').json()
    assert report['descriptive_sensitivity'] is None and report['descriptive_specificity'] is None
    assert report['counts']['unlabelled']==1


def test_short_wfdb_record_excluded(client):
    storage.save(RecordCreate(title='Short test fixture',origin='wfdb_research',sample_rate_hz=250,
        reference_label='True',channels=[Channel(kind='ECG',name='II',unit='mV',samples=[0.01]*100)]))
    response=client.post('/api/pilot/sessions',json={'reviewer_code':'reviewer-01'})
    assert response.status_code==422
    assert '300-second' in response.text
