"""Synthetic research tests for event-window evidence, not clinical validation."""
from pathlib import Path
import math
import shutil
import subprocess
import pytest
from waveassure.schemas import Channel, RecordCreate
from waveassure.event_context import describe_at

ROOT=Path(__file__).resolve().parents[1]


def example(origin='wfdb_research', label='True', source='dataset_annotation',
            event_time=2.0, parent_id=None):
    return RecordCreate(
        title='Synthetic fixture', sample_rate_hz=100, origin=origin,
        source_reference='Test VTaC research annotation (synthetic fixture)',
        reference_label=label,
        alarm_time_s=event_time, alarm_time_source=source if event_time is not None else None,
        channels=[
            Channel(kind='ECG',name='II',unit='mV',samples=[float(i % 3) if i != 200 else None for i in range(400)]),
            Channel(kind='ECG',name='aVR',unit='mV',samples=[0.1]*400),
            Channel(kind='PPG',name='PLETH',unit='NU',samples=[0.4]*400),
            Channel(kind='ABP',name='ABP',unit='mmHg',samples=[91.0]*400)
        ]), {'parent_id': parent_id}


def test_source_vt_label_and_all_channel_observations():
    r,m=example()
    result=describe_at(r,m,2.0)
    assert result['reference_event']=='genuine_vt_alarm'
    assert 'source ALARM category' in result['reference_rhythm_category']
    assert len(result['channels'])==4
    assert [c['kind'] for c in result['channels']]==['ECG','ECG','PPG','ABP']
    assert result['channels'][0]['missing_samples']==1
    assert result['channels'][0]['valid_samples']==399
    assert result['channels'][0]['minimum']==0.0
    assert result['channels'][0]['maximum']==2.0
    assert result['channels'][2]['unit']=='NU'
    assert result['channels'][3]['unit']=='mmHg'
    for c in result['channels']:
        assert c['physiological_status']=='NOT_ASSESSED'
        assert c['ecg_morphology']=='NOT_CLASSIFIED' if c['kind']=='ECG' else c['ecg_morphology']=='NOT_APPLICABLE'
    assert result['clinical_assessment']=='NOT_PERFORMED'


def test_false_reference_not_normal_and_user_time_not_adjudicated():
    r,m=example(label='False')
    result=describe_at(r,m,2.0)
    assert result['reference_event']=='false_vt_alarm'
    assert all(c['physiological_status']=='NOT_ASSESSED' for c in result['channels'])
    user,m=example(label='True',source='user_annotation_unverified')
    result=describe_at(user,m,2.0)
    assert result['reference_event']=='unverified_user_time_cause_unknown'
    assert result['reference_rhythm_category'] is None


def test_demonstration_time_not_real_alarm_and_derived_not_inherited():
    r,m=example(event_time=None,source='dataset_annotation',origin='synthetic')
    assert describe_at(r,m,2.0)['reference_event']=='no_supported_event_reference'
    orig,_=example()
    result=describe_at(orig,{'parent_id':'original'},2.0)
    assert result['reference_event']=='no_supported_event_reference'


def test_window_bounds_and_nonfinite_time():
    r,m=example()
    assert describe_at(r,m,0.0)['window_start_s']==0
    assert describe_at(r,m,4.0)['window_end_s']==4.0
    for bad in [-0.01,4.01,math.nan,math.inf]:
        with pytest.raises(ValueError):
            describe_at(r,m,bad)
    for bad in [0.0,-1.0,6,math.nan]:
        with pytest.raises(ValueError):
            describe_at(r,m,2.0,radius_s=bad)


def test_event_context_endpoint(client):
    response=client.post('/api/demo?kind=baseline')
    assert response.status_code==201,response.text
    ident=response.json()['id']
    good=client.get('/api/records/'+ident+'/event-context?at_s=5')
    assert good.status_code==200,good.text
    body=good.json()
    assert body['reference_event']=='no_supported_event_reference'
    assert body['clinical_assessment']=='NOT_PERFORMED'
    assert len(body['channels'])==3
    assert all(c['physiological_status']=='NOT_ASSESSED' for c in body['channels'])
    assert client.get('/api/records/'+ident+'/event-context?at_s=-1').status_code==422
    assert client.get('/api/records/'+ident+'/event-context?at_s=15').status_code==422
    assert client.get('/api/records/not-a-record/event-context?at_s=2').status_code in (404,409)


@pytest.mark.skipif(not shutil.which('node'), reason='Node unavailable')
def test_frontend_event_source_contract():
    result=subprocess.run(['node',str(ROOT/'tests'/'event-context20.cjs')],
                         capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert 'PASS' in result.stdout
