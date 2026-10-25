"""CSV safety regressions use synthetic values only; not clinical validation."""
import shutil
import subprocess
from pathlib import Path
import pytest
from waveassure.csv_input import parse_csv, is_non_waveform_column
from waveassure.schemas import CSVImport


def _body(headers, rows=120):
    return ','.join(headers)+'\n'+''.join(
        f'{i / 100:.2f},' + ','.join('1' for _ in headers[1:]) + '\n'
        for i in range(rows))


def _mapped(csv_text, kind='ECG', column='ECG_mV'):
    return CSVImport(title='research only', csv_text=csv_text,
        time_column='time_s', time_unit='s',
        channel_mapping=[{'column':column,'name':'Channel','kind':kind,'unit':'mV'}])


def test_patient_number_header_rejected_even_if_not_selected():
    content=_body(['time_s','ECG_mV','Patient Number'])
    with pytest.raises(ValueError,match='Identifying column headers'):
        parse_csv(_mapped(content))


@pytest.mark.parametrize('column', ['Heart Rate Alert','SpO2 Level Alert',
    'Blood Pressure Alert','Data Accuracy (%)','ECG Alarm',
    'Heart Rate','SpO2','Respiratory Rate'])
def test_summary_data_cannot_masquerade_as_ecg_samples(column):
    assert is_non_waveform_column(column)
    with pytest.raises(ValueError,match='cannot be mapped as waveform samples'):
        parse_csv(_mapped(_body(['time_s',column]),column=column))


def test_real_ecg_waveform_import_still_accepted():
    record=parse_csv(_mapped(_body(['time_s','ECG_mV'])))
    assert record.sample_rate_hz==pytest.approx(100)
    assert len(record.channels[0].samples)==120
    assert record.alarm_time_s is None
    assert record.origin=='local_csv_unverified'


@pytest.mark.skipif(not shutil.which('node'),reason='Node not installed')
def test_csv_browser_mapping_safeguards():
    script=Path(__file__).resolve().parent/'csv-guard16.cjs'
    result=subprocess.run(['node',str(script)],capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    assert 'verified' in result.stdout
