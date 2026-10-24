"""Engineering fixtures are synthetic. No clinical or VTaC accuracy claims."""
import json
import numpy as np
import pytest
from waveassure.alarm_model import FEATURE_NAMES, extract_features, read_model, assess, features_from_record
from benchmarks.train_vtac import train, split_rows, audit_data, verify_format16_waveform
from waveassure.signals import demo_record


def test_feature_schema_on_six_minute_signal():
    fs=250
    t=np.arange(90000)/fs
    data=np.column_stack([np.sin(2*np.pi*1.8*t),-np.sin(2*np.pi*1.8*t),np.sin(2*np.pi*1.8*t+.4)])
    f=extract_features(data,['II','aVR','PLETH'],fs)
    assert len(f)==len(FEATURE_NAMES)==16
    assert f[0]==0 and f[6]==0
    assert f[12]==0


def test_no_post_alarm_leakage():
    fs=100
    t=np.arange(31000)/fs
    x=np.sin(2*np.pi*2*t)
    d=np.column_stack([x,np.cos(2*np.pi*t)])
    first=np.array(extract_features(d,['II','PLETH'],fs))
    d[int(300*fs):] += 99999
    second=np.array(extract_features(d,['II','PLETH'],fs))
    assert np.allclose(first,second,equal_nan=True)


def test_reject_short_record():
    with pytest.raises(ValueError,match='At least 300'):
        extract_features(np.ones((1000,1)),['II'],250)


def test_refuse_single_true_event_and_missing_splits(tmp_path):
    X=np.ones((1,len(FEATURE_NAMES)))
    with pytest.raises(ValueError, match='both True and False'):
        train(X,np.array([1]),np.array(['train']),['623dd0/623dd0_0023'],tmp_path/'model')
    assert not (tmp_path/'model'/'vt_model.json').exists()


def test_synthetic_software_training_export_and_checksum(tmp_path):
    from sklearn.linear_model import LogisticRegression
    rng=np.random.default_rng(15)
    # Synthetic numeric engineering fixture only: does NOT represent patient features.
    X=rng.normal(size=(60,len(FEATURE_NAMES)))
    y=np.array([0,1]*30)
    X[:,0]+=y*1.4
    X[1,3]=np.nan
    parts=np.array(['train']*36+['validation']*12+['test']*12)
    model_dir=tmp_path/'models'
    output=train(X,y,parts,[f'p{i}/e{i}' for i in range(len(y))],model_dir,smoke=True)
    assert output['research_only'] is True
    mod=read_model(model_dir/'vt_model.json', internal_smoke_test=True)
    with pytest.raises(ValueError, match='smoke-test models'):
        read_model(model_dir/'vt_model.json')
    result=assess(mod,X[5].tolist())
    assert 0 <= result['research_probability_true_vt'] <=1
    assert 'not a verified clinical probability' in result['limitations'].lower()
    obj=json.loads((model_dir/'vt_model.json').read_text())
    obj['coefficients'][0] +=1
    (model_dir/'vt_model.json').write_text(json.dumps(obj))
    with pytest.raises(ValueError, match='checksum'):
        read_model(model_dir/'vt_model.json')


def test_api_model_not_installed_and_no_synthetic_assessment(client):
    status=client.get('/api/research-model/status')
    assert status.status_code==200 and status.json()['available'] is False
    demo=client.post('/api/demo?kind=baseline').json()['id']
    response=client.post('/api/records/'+demo+'/research-assessment')
    assert response.status_code==409


def test_checksum_guard_for_benchmark_loader(tmp_path):
    base=tmp_path/'p_01'
    data=np.arange(300,dtype=np.int16).reshape(100,3)
    data.tofile(base.with_suffix('.dat'))
    lines=['p_01 3 250 100']
    for idx,lead in enumerate(('II','aVR','PLETH')):
        checksum=int(np.sum(data[:,idx],dtype=np.int64)) &65535
        lines.append(f'p_01.dat 16 1000(0)/mV 16 0 0 {checksum} 0 {lead}')
    base.with_suffix('.hea').write_text('\n'.join(lines)+'\n')
    assert verify_format16_waveform(str(base)) is True
    raw=bytearray(base.with_suffix('.dat').read_bytes());raw[0]^=1
    base.with_suffix('.dat').write_bytes(raw)
    with pytest.raises(ValueError,match='checksum'):
        verify_format16_waveform(str(base))


def test_reject_patient_overlap_in_direct_trainer(tmp_path):
    X=np.ones((3,len(FEATURE_NAMES)))
    with pytest.raises(ValueError, match='Patient-record leakage'):
        train(X,np.array([1,0,1]),np.array(['train','validation','test']),
              ['shared/event1','shared/event2','other/event3'],tmp_path/'models',smoke=True)


def test_reject_duplicate_event_in_direct_trainer(tmp_path):
    X=np.ones((3,len(FEATURE_NAMES)))
    with pytest.raises(ValueError, match='Duplicate dataset event'):
        train(X,np.array([1,0,1]),np.array(['train','train','test']),
              ['shared/event1','shared/event1','other/event3'],tmp_path/'models',smoke=True)
