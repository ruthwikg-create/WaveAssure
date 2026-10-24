"""Synthetic WFDB fixtures intentionally mimic the published VTaC format-16 header."""
import csv
import numpy as np
from waveassure.wfdb_input import import_local_wfdb
from waveassure.signals import analyze, inject_fault, preview
from waveassure.schemas import FaultRequest


def make_fixture(tmp_path, monkeypatch):
    monkeypatch.setenv('WAVEASSURE_WFDB_ROOT', str(tmp_path))
    directory = tmp_path / 'sample' / '623dd0'
    directory.mkdir(parents=True)
    record = '623dd0_0023'
    samples = np.zeros((1000,4),dtype=np.int16)
    samples[:,0] = np.arange(1000,dtype=np.int16)%120 + 6800
    samples[:,1] = -(np.arange(1000,dtype=np.int16)%120) - 500
    samples[:,2] = np.arange(1000,dtype=np.int16)%200 - 7500
    samples[:,3] = np.arange(1000,dtype=np.int16)%300 - 15000
    dat=directory/f'{record}.dat'
    samples.astype('<i2').tofile(dat)
    descriptions=[('25953.44262295082(6812)/mV','II'),('35044.565217391304(-526)/mV','aVR'),
        ('37771.64179104477(-7460)/mV','V'),('65566.01465559355(-32767)/NU','PLETH')]
    lines=[f'{record} 4 250 1000']
    for i, (calibration, name) in enumerate(descriptions):
        checksum=int(np.sum(samples[:,i],dtype=np.int64)) & 65535
        lines.append(f'{record}.dat 16 {calibration} 16 0 {int(samples[0,i])} {checksum} 0 {name}')
    (directory/f'{record}.hea').write_text('\n'.join(lines)+'\n',encoding='ascii')
    with (tmp_path/'event_labels.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['record','event','decision'])
        writer.writeheader();writer.writerow({'record':'623dd0','event':record,'decision':'True'})
    return 'sample/623dd0/623dd0_0023',dat


def test_import_four_channels_and_calibration(tmp_path,monkeypatch):
    path,dat=make_fixture(tmp_path,monkeypatch)
    obj=import_local_wfdb(path)
    assert obj.origin=='wfdb_research'
    assert obj.reference_label=='True'
    assert obj.sample_rate_hz==250
    assert [c.name for c in obj.channels]==['II','aVR','V','PLETH']
    assert [c.unit for c in obj.channels]==['mV','mV','mV','NU']
    assert abs(obj.channels[0].samples[0] - (6800-6812)/25953.44262295082)<1e-10
    assert len(obj.channels[3].samples)==1000
    summary=analyze(obj)
    assert len(summary['quality_checks'])==4
    assert all(c['estimated_bpm'] is None for c in summary['quality_checks'])  # unvalidated clinical-looking number withheld
    assert summary['alarm_classification']['status']=='NOT_AVAILABLE'
    assert all(x['t']==preview(obj,max_points=140)[0]['t'] for x in preview(obj,max_points=140))
    before=list(obj.channels[1].samples)
    altered=inject_fault(obj,FaultRequest(kind='dropout',target='aVR'))
    assert obj.channels[1].samples==before
    assert any(v is None for v in altered.channels[1].samples)
    assert altered.channels[0].samples==obj.channels[0].samples
    assert altered.reference_label=='Unlabeled'  # derived signal must not inherit dataset annotation


def test_reject_truncated_file(tmp_path,monkeypatch):
    path,dat=make_fixture(tmp_path,monkeypatch)
    dat.write_bytes(dat.read_bytes()[:100])
    import pytest
    with pytest.raises(ValueError,match='Incomplete'):
        import_local_wfdb(path)


def test_reject_corrupted_samples(tmp_path,monkeypatch):
    path,dat=make_fixture(tmp_path,monkeypatch)
    raw=bytearray(dat.read_bytes())
    raw[2]=raw[2]^0x01
    dat.write_bytes(raw)
    import pytest
    with pytest.raises(ValueError,match='checksum mismatch'):
        import_local_wfdb(path)


def test_reject_path_traversal(tmp_path,monkeypatch):
    make_fixture(tmp_path,monkeypatch)
    import pytest
    for bad in ('../secrets','C:/Windows/System32/file','sample/623dd0/../../x','https://example.com/x'):
        with pytest.raises(ValueError):
            import_local_wfdb(bad)


def test_api_import_and_window(client, tmp_path, monkeypatch):
    path, dat=make_fixture(tmp_path,monkeypatch)
    response=client.post('/api/import-wfdb',json={'record_path':path})
    assert response.status_code==201, response.text
    obj_id=response.json()['id']
    loaded=client.get('/api/records/'+obj_id).json()
    assert len(loaded['waveforms'])==4
    assert loaded['reference_label']=='True'
    assert loaded['waveforms'][0]['name']=='II'
    data=client.get(f'/api/records/{obj_id}/preview?start_s=1&window_s=2')
    assert data.status_code==200
    assert data.json()['waveforms'][0]['t'][0]>=1
    failed=client.post('/api/import-wfdb',json={'record_path':'../nope'})
    assert failed.status_code==422
    assert client.get('/api/records/'+obj_id+'/report').json()['reference_annotation']['label']=='True'
