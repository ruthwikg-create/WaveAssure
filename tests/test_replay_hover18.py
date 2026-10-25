"""Research-only regression tests for replay controls and reproducible sample CSV."""
from pathlib import Path
import runpy
import shutil
import subprocess

import pytest
from waveassure.csv_input import parse_csv
from waveassure.schemas import CSVImport

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which('node') is None, reason='Node required in CI')
def test_timeline_and_alarm_hover_unit_scenarios():
    result = subprocess.run(['node', str(ROOT/'tests'/'replay-hover18.cjs')],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert '24 unit/contract assertions passed' in result.stdout


def test_generated_deidentified_synthetic_csv_loads(tmp_path):
    script = runpy.run_path(str(ROOT/'scripts'/'generate-research-waveform-csv.py'))
    dest = script['write_example'](tmp_path/'synthetic_test.csv')
    data = dest.read_text(encoding='utf-8')
    assert data.startswith('time_s,ECG_mV,PPG_au,ABP_mmHg')
    rec = parse_csv(CSVImport(title='Synthetic test, not patient data', csv_text=data))
    assert rec.origin == 'local_csv_unverified'
    assert rec.sample_rate_hz == pytest.approx(100)
    assert len(rec.channels) == 3
    assert len(rec.channels[0].samples) == 2000
    assert rec.alarm_time_s is None
    assert rec.alarm_time_source is None
    assert rec.reference_label == 'Unlabeled'


def test_no_unsupported_clinical_inference_in_replay():
    app = (ROOT/'web'/'app.js').read_text(encoding='utf-8')
    html = (ROOT/'web'/'index.html').read_text(encoding='utf-8')
    assert 'if(\u0024(\'alarmTone\').checked)simulatedTone()' in app
    assert 'No original alarm sound or automatic diagnosis' in html
    assert 'WaveAssureReplay.crossedEvent' in app
    assert 'datasetFormatGuide' in html
