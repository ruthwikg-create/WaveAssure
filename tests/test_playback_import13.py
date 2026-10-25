"""Waveform timeline and custom-file import regressions; synthetic fixtures only."""
import base64
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from waveassure.api import app
from waveassure.schemas import CSVImport, RecordCreate, Channel
from waveassure.csv_input import parse_csv
from waveassure.evidence import create_evidence
from tests.test_wfdb_import import make_fixture


def test_mapped_csv_custom_columns_and_alarm_time():
    body='Time (ms),LeadII,Pleth,DeviceFlag\n'+''.join(f'{i*10},{i%25},{i%7},OK\n' for i in range(120))
    payload=CSVImport(title='Custom waveform', csv_text='\ufeff'+body,
        time_column='Time (ms)', time_unit='ms', alarm_time_s=.75,
        channel_mapping=[{'column':'LeadII','name':'II','kind':'ECG','unit':'mV'},
                         {'column':'Pleth','name':'PLETH','kind':'PPG','unit':'NU'}])
    record=parse_csv(payload)
    assert record.sample_rate_hz==pytest.approx(100)
    assert record.alarm_time_s==.75
    assert record.alarm_time_source=='user_annotation_unverified'
    assert [c.name for c in record.channels]==['II','PLETH']
    doc=create_evidence(record,{'id':'x','title':'test','origin':record.origin,'parent_id':None,
                                'data_sha256':'aa'*32,'fault':None}, {'ok':True})
    assert doc['reference_annotation']['event_time_s']==.75
    assert doc['reference_annotation']['event_type'] is None
    assert doc['reference_annotation']['type']=='NOT_AVAILABLE'
    assert doc['descriptive_measurements']['pre_alarm_30s']['end_s']==.75


def test_csv_custom_rejects_identifier_and_bogus_units():
    mapped=[{'column':'LeadII','name':'II','kind':'ECG','unit':'mV'}]
    data='Tick,LeadII,patient_ID\n'+''.join(f'{i*10},{i},alice\n' for i in range(100))
    with pytest.raises(ValueError,match='Identifying|identifying'):
        parse_csv(CSVImport(title='x',csv_text=data,time_column='Tick',time_unit='ms',channel_mapping=mapped))
    with pytest.raises(ValueError,match='ECG must have'):
        parse_csv(CSVImport(title='x',csv_text='Tick,LeadII\n'+''.join(f'{i*10},{i}\n' for i in range(100)),time_column='Tick',time_unit='ms',channel_mapping=[{'column':'LeadII','name':'II','kind':'ECG','unit':'mmHg'}]))


def test_custom_file_pair_upload_has_no_verified_reference(client, monkeypatch, tmp_path):
    path,dat=make_fixture(tmp_path,monkeypatch)
    hea=dat.with_suffix('.hea')
    payload={'header_filename':hea.name, 'header_text':hea.read_text(), 'data_filename':dat.name,
             'data_base64':base64.b64encode(dat.read_bytes()).decode('ascii'), 'alarm_time_s':2.0}
    result=client.post('/api/import-wfdb-files',json=payload)
    assert result.status_code==201, result.text
    record=client.get('/api/records/'+result.json()['id']).json()
    assert record['alarm_time_s']==2.0
    assert record['alarm_time_source']=='user_annotation_unverified'
    assert record['reference_label']=='Unlabeled'
    assert record['waveforms'][0]['name']=='II'
    evidence=client.get('/api/records/'+result.json()['id']+'/evidence').json()
    assert evidence['reference_annotation']['label']=='Unlabeled'
    assert evidence['reference_annotation']['event_time_source']=='user_annotation_unverified'


def test_reject_custom_wfdb_wrong_name_checksum_and_annotation(client,monkeypatch,tmp_path):
    _,dat=make_fixture(tmp_path,monkeypatch)
    hea=dat.with_suffix('.hea'); bytes_data=dat.read_bytes()
    base={'header_filename':hea.name,'header_text':hea.read_text(),
          'data_filename':dat.name,'data_base64':base64.b64encode(bytes_data).decode()}
    bad={**base, 'data_filename':'wrong.dat'}
    assert client.post('/api/import-wfdb-files',json=bad).status_code==422
    corrupted=bytearray(bytes_data);corrupted[40]^=0xff
    bad={**base, 'data_base64':base64.b64encode(corrupted).decode()}
    r=client.post('/api/import-wfdb-files',json=bad)
    assert r.status_code==422 and 'checksum' in r.text.lower()
    bad={**base,'alarm_time_s':10.0}
    assert client.post('/api/import-wfdb-files',json=bad).status_code==422
    assert client.post('/api/import-wfdb-files',json={**base, 'data_base64':'@@@'}).status_code==422


def test_local_vtac_label_on_short_fixture_has_no_fabricated_time(tmp_path,monkeypatch):
    from waveassure.wfdb_input import import_local_wfdb
    path,_=make_fixture(tmp_path,monkeypatch)
    record=import_local_wfdb(path)
    assert record.reference_label=='True'
    assert record.alarm_time_s is None  # fixture is 4 seconds, not the original six-minute event


def test_custom_dataset_never_forges_model_label(client):
    r=client.post('/api/records',json={'title':'Synthetic input','sample_rate_hz':100,'origin':'synthetic',
           'reference_label':'True','alarm_time_s':0.5,'alarm_time_source':'dataset_annotation',
           'channels':[{'kind':'ECG','name':'II','unit':'mV','samples':[0.0]*100}]})
    assert r.status_code==201,r.text
    record=client.get('/api/records/'+r.json()['id']).json()
    assert record['reference_label']=='Unlabeled'
    assert record['alarm_time_s'] is None
    assert record['alarm_time_source'] is None


def test_static_ui_playback_and_dataset_mapping_exists():
    base=Path(__file__).resolve().parents[1]/'web'
    ui=(base/'index.html').read_text()
    code=(base/'app.js').read_text()
    for marker in ('replayToggle','windowStart','alarmDetail','jumpAlarm','replaySpeed','csvMapper',
                   'csvTimeColumn','csvChannels','datasetFiles','importWFDBFiles'):
        assert f'id="{marker}"' in ui
    assert 'requestAnimationFrame(replayStep)' in code
    assert 'alarm_time_s' in code and 'user_annotation_unverified' in code
    assert 'draw(canvas,w,{hideAlarm:true})' in code


def test_vtac_full_length_alarm_annotation_is_300_seconds(tmp_path, monkeypatch):
    import csv
    import numpy as np
    from waveassure.wfdb_input import import_local_wfdb
    monkeypatch.setenv('WAVEASSURE_WFDB_ROOT', str(tmp_path))
    folder=tmp_path/'sample'/'example';folder.mkdir(parents=True)
    base='example_0001';n=360*250
    d=np.full(n,6800,dtype='<i2')
    (folder/(base+'.dat')).write_bytes(d.tobytes())
    checksum=int(d.astype(np.int64).sum()) & 65535
    (folder/(base+'.hea')).write_text(f'{base} 1 250 {n}\n{base}.dat 16 200(6800)/mV 16 0 6800 {checksum} 0 II\n',encoding='ascii')
    with (tmp_path/'event_labels.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=['record','event','decision'])
        writer.writeheader();writer.writerow({'record':'example','event':base,'decision':'True'})
    record=import_local_wfdb('sample/example/example_0001')
    assert record.alarm_time_s==300.0
    assert record.alarm_time_source=='dataset_annotation'
    assert record.reference_label=='True'
    assert len(record.channels[0].samples)==90000
    assert record.sample_rate_hz==250
    metadata={'id':'x','title':'test','origin':record.origin,'parent_id':None,
              'data_sha256':'ab'*32,'fault':None}
    doc=create_evidence(record,metadata,{'ok':True})
    assert doc['reference_annotation']['event_time_s']==300.0
    assert doc['descriptive_measurements']['pre_alarm_30s']['start_s']==270.0
    assert doc['descriptive_measurements']['post_alarm_30s']['end_s']==330.0


def test_unknown_wfdb_alarm_stays_unknown_even_when_long(tmp_path, monkeypatch):
    import numpy as np
    from waveassure.wfdb_input import import_local_wfdb
    monkeypatch.setenv('WAVEASSURE_WFDB_ROOT',str(tmp_path))
    n=400*100;name='record001'
    x=np.zeros(n,dtype='<i2')
    (tmp_path/(name+'.dat')).write_bytes(x.tobytes())
    (tmp_path/(name+'.hea')).write_text(f'{name} 1 100 {n}\n{name}.dat 16 200/mV 16 0 0 0 0 II\n')
    rec=import_local_wfdb(name)
    assert rec.alarm_time_s is None
    assert rec.reference_label=='Unlabeled'
    report=create_evidence(rec,{'id':'r','title':'r','origin':rec.origin,'parent_id':None,'data_sha256':'ab'*32,'fault':None},{'ok':True})
    assert report['reference_annotation']['event_time_s'] is None
    assert 'pre_alarm_30s' not in report['descriptive_measurements']
