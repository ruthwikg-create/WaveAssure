import pytest
from waveassure.csv_input import parse_csv
from waveassure.schemas import CSVImport

def sample(header='time_s,ECG_mV',extra=''):
    return header+'\n'+''.join(f'{i/250},{i%11}{extra}\n' for i in range(100))

def test_csv_success():
    r=parse_csv(CSVImport(title='local',csv_text=sample()))
    assert r.origin=='local_csv_unverified'
    assert r.sample_rate_hz==pytest.approx(250)

def test_identifying_headers_rejected():
    with pytest.raises(ValueError,match='Unsupported columns'):
        parse_csv(CSVImport(title='bad',csv_text='time_s,ECG_mV,patient_name\n'+''.join(f'{i/250},0,Alice\n' for i in range(100))))

def test_irregular_sampling_rejected():
    s='time_s,ECG_mV\n'+''.join(f'{i/250+(0.5 if i==50 else 0)},{i}\n' for i in range(100))
    with pytest.raises(ValueError):parse_csv(CSVImport(title='bad',csv_text=s))

def test_nonfinite_values_rejected():
    with pytest.raises(ValueError):parse_csv(CSVImport(title='bad',csv_text=sample().replace('0,0\n','0,NaN\n',1)))
