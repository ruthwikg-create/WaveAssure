"""Risk-based output verification tests for research evidence exports."""
from waveassure.evidence import create_evidence, window_statistics
from waveassure.schemas import RecordCreate, Channel
from waveassure.signals import demo_record


def meta(origin='synthetic', parent_id=None):
    return {'id':'r-123', 'title':'test', 'origin':origin,'parent_id':parent_id,
            'fault':None, 'data_sha256':'ab'*32}


def test_descriptive_statistics_are_grounded_and_missing_never_interpolated():
    record=RecordCreate(title='fixture',sample_rate_hz=100,origin='synthetic',
                        channels=[Channel(kind='ECG',name='II',unit='mV', samples=[None]*20 + [1.0]*80)])
    one=window_statistics(record,0,1)['channels'][0]
    assert one['total_samples']==100
    assert one['valid_samples']==80
    assert one['missing_samples']==20
    assert one['missing_fraction']==.2
    assert one['mean']==1.0
    assert one['minimum']==one['maximum']==1.0


def test_empty_window_never_claims_mean_or_quality():
    r=demo_record('baseline')
    result=window_statistics(r,20,30)
    assert not result['data_window_available']
    assert result['channels'][0]['mean'] is None
    assert result['channels'][0]['missing_fraction'] is None


def test_synthetic_never_claims_vt_ground_truth_or_diagnosis():
    r=demo_record('tachy_simulation')
    report=create_evidence(r,meta(),{'ok':True})
    assert report['data_class']=='SYNTHETIC'
    assert report['reference_annotation']['type']=='NOT_AVAILABLE'
    assert report['decision_support']['clinical_interpretation'] is None
    assert report['decision_support']['clinical_alarm_assessment']=='NOT_PERFORMED'
    assert report['integrity']['official_dataset_sha256_verified'] is False
    assert report['integrity']['audit_log_is_digitally_signed'] is False


def test_derived_wfdb_never_claims_source_reference():
    r=RecordCreate(title='fault', sample_rate_hz=100,origin='wfdb_research',reference_label='True',
                   channels=[Channel(kind='ECG',name='II',unit='mV',samples=[0.0]*100)])
    report=create_evidence(r,meta('wfdb_research','source-id'),{'ok':False})
    assert report['reference_annotation']['label']=='Unlabeled'
    assert report['integrity']['audit_chain_currently_valid'] is False
    assert report['integrity']['format_level_check_at_import'] is False


def test_real_six_minute_event_window_edges():
    fs=100
    samples=[0.0]* (270*fs) + [1.0]*(30*fs)+ [2.0]*(30*fs)+[3.0]*(30*fs)
    r=RecordCreate(title='record',sample_rate_hz=fs,origin='wfdb_research',reference_label='True',
                   source_reference='VTaC reference fixture',
                   channels=[Channel(kind='ECG',name='II',unit='mV',samples=samples)])
    report=create_evidence(r,meta('wfdb_research'),{'ok':True})
    pre=report['descriptive_measurements']['pre_alarm_30s']
    post=report['descriptive_measurements']['post_alarm_30s']
    assert pre['start_s']==270 and pre['end_s']==300
    assert post['start_s']==300 and post['end_s']==330
    assert pre['channels'][0]['mean']==1
    assert post['channels'][0]['mean']==2
    assert report['reference_annotation']['event_time_s']==300
    assert report['reference_annotation']['independently_verified_by_waveassure'] is False


def test_api_evidence_matches_report_and_hides_spurious_diagnoses(client):
    response=client.post('/api/demo?kind=baseline');rid=response.json()['id']
    embedded=client.get('/api/records/'+rid+'/evidence')
    downloaded=client.get('/api/records/'+rid+'/report')
    assert embedded.status_code==200
    assert downloaded.status_code==200
    assert 'attachment' in downloaded.headers['content-disposition']
    assert embedded.json()['record']['payload_sha256']==downloaded.json()['record']['payload_sha256']
    assert downloaded.json()['reference_annotation']['label']=='Unlabeled'
    assert downloaded.json()['decision_support']['alarm_prioritization'] is None


def test_fault_derived_record_loses_original_expert_label(client,monkeypatch,tmp_path):
    from tests.test_wfdb_import import make_fixture
    path, _=make_fixture(tmp_path,monkeypatch)
    source=client.post('/api/import-wfdb',json={'record_path':path})
    assert source.status_code==201
    rid=source.json()['id']
    changed=client.post(f'/api/records/{rid}/fault',json={'kind':'dropout','target':'aVR','severity':.5})
    assert changed.status_code==201
    dest=changed.json()['id']
    assert client.get(f'/api/records/{dest}').json()['reference_label']=='Unlabeled'
    assert client.get(f'/api/records/{dest}/report').json()['reference_annotation']['label']=='Unlabeled'


def test_printable_report_escapes_input_and_is_not_clinical(client):
    from waveassure.report_html import report_html
    r=demo_record('baseline')
    r.title='<script>alert(1)</script>'
    m=meta();m['title']=r.title
    report=create_evidence(r,m,{'ok':True})
    html=report_html(report)
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
    assert 'RESEARCH USE ONLY' in html
    assert 'No medical decision provided' in html


def test_printable_html_route(client):
    rid=client.post('/api/demo?kind=baseline').json()['id']
    resp=client.get(f'/api/records/{rid}/report.html')
    assert resp.status_code==200
    assert 'text/html' in resp.headers['content-type']
    assert 'RESEARCH USE ONLY' in resp.text
    assert 'SYNTHETIC' in resp.text


def test_fault_data_class_is_derived_not_original_wfdb():
    r=RecordCreate(title='fault',sample_rate_hz=100,origin='wfdb_research',
                    channels=[Channel(kind='ECG',name='II',unit='mV',samples=[1.0]*100)])
    doc=create_evidence(r,meta('wfdb_research','id'),{'ok':True})
    assert doc['data_class']=='DERIVED_FAULT_EXPERIMENT'
