import pytest
from waveassure.signals import demo_record, analyze,inject_fault,preview
from waveassure.schemas import FaultRequest, RecordCreate, Channel

def test_synthetic_baseline_has_three_channels():
    r=demo_record('baseline')
    assert [c.kind for c in r.channels]==['ECG','PPG','ABP']
    result=analyze(r)
    assert result['alarm_classification']['status']=='NOT_AVAILABLE'
    assert result['duration_s']==12.0

def test_synthetic_stable_output():
    assert demo_record('baseline').model_dump()==demo_record('baseline').model_dump()

def test_dropout_is_flagged_and_source_preserved():
    original=demo_record('baseline');first=original.channels[0].samples[:]
    transformed=inject_fault(original,FaultRequest(kind='dropout',target='ECG',severity=.7))
    assert original.channels[0].samples==first
    assert any(x is None for x in transformed.channels[0].samples)
    assert analyze(transformed)['status']=='REVIEW_REQUIRED'
    assert analyze(transformed)['quality_checks'][0]['missing_pct']>=2.

def test_mains_interference_increases_noise():
    r=demo_record('baseline');f=inject_fault(r,FaultRequest(kind='mains_interference',target='ECG',severity=1))
    before=analyze(r)['quality_checks'][0]['mains_ratio']
    after=analyze(f)['quality_checks'][0]['mains_ratio']
    assert after > before

def test_preview_has_same_time_grid():
    r=demo_record('baseline');x=preview(r,200)
    assert len(x[0]['values'])<=200
    assert x[0]['t']==x[1]['t']

def test_reject_incorrect_units():
    with pytest.raises(ValueError):Channel(kind='ECG',unit='mmHg',samples=[0.]*100)

def test_reject_mismatched_lengths():
    with pytest.raises(ValueError):RecordCreate(title='wrong',origin='synthetic',sample_rate_hz=250,
      channels=[Channel(kind='ECG',unit='mV',samples=[0.]*100),Channel(kind='PPG',unit='a.u.',samples=[1.]*200)])

def test_reject_missing_fault_channel():
    r=demo_record('baseline');r.channels=r.channels[:1]
    with pytest.raises(ValueError):inject_fault(r,FaultRequest(kind='dropout',target='PPG'))
