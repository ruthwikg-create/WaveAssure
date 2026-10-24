import pytest
import numpy as np
from benchmarks.prepare_and_train import resumable,select_subset
from benchmarks.train_vtac import physical_pre_alarm_window,verify_format16_waveform,validation_threshold


def test_reject_unofficial_remote(tmp_path):
    with pytest.raises(ValueError):resumable('https://elsewhere.com/wave.dat',tmp_path/'x',retries=1)


def test_select_balanced_official_split(tmp_path):
    rows=[{'record':f'{part}_{lab}_{i}','event':f'e{i}', 'partition':part,'y':lab}
         for part in ('train','validation','test') for lab in (0,1) for i in range(25)]
    got=select_subset(rows,tmp_path)
    assert len(got)==76
    assert len({x['record'] for x in got})==76
    assert sum(x['y']==1 for x in got)==38


def test_pre_alarm_physical_units_and_checksum(tmp_path):
    p=tmp_path/'r';(tmp_path/'r.hea').write_text('r 3 250 90000\n'+
        'r.dat 16 1000(0)/mV 16 0 0 0 0 II\n'+
        'r.dat 16 1000(0)/mV 16 0 0 0 0 aVR\n'+
        'r.dat 16 1000(0)/NU 16 0 0 0 0 PLETH\n')
    x=np.zeros((90000,3),dtype='<i2');x[67500,0]=1000;x[67501,0]=-1000
    x.tofile(p.with_suffix('.dat'))
    assert verify_format16_waveform(p)
    data,names,fs=physical_pre_alarm_window(p)
    assert data.shape==(7500,3) and names==['II','aVR','PLETH']
    assert data[0,0]==1 and data[1,0]==-1 and fs==250
    with p.with_suffix('.dat').open('r+b') as out:out.write(b'\x01\x00')
    with pytest.raises(ValueError,match='checksum'):verify_format16_waveform(p)


def test_validation_threshold_sensitivity():
    threshold,info=validation_threshold(np.array([1,1,0,0]),np.array([.95,.81,.80,.1]),target=1.0)
    assert threshold<=.81 and info['reached']
