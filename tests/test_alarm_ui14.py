"""UI explanation guardrails only, not clinical validation."""
from pathlib import Path
import shutil
import subprocess
import pytest

WEB=Path(__file__).resolve().parents[1]/'web'


def test_explainer_never_infers_diagnosis_from_samples():
    js=(WEB/'alarm-event.js').read_text(encoding='utf-8')
    assert "meta.origin === 'wfdb_research'" in js
    assert "record.alarm_time_source === 'dataset_annotation'" in js
    assert "record.alarm_time_source === 'user_annotation_unverified'" in js
    assert 'does NOT establish a normal heart rhythm' in js
    assert 'No verified VT reference decision' in js
    assert 'WaveAssure has not classified this recording' in js


def test_accessible_alarm_interaction_and_motion_semantics():
    html=(WEB/'index.html').read_text(encoding='utf-8')
    script=(WEB/'app.js').read_text(encoding='utf-8')
    theme=(WEB/'theme.js').read_text(encoding='utf-8')
    assert 'id="explainAlarm"' in html
    assert 'id="alarmExplanation"' in html
    assert html.index('/static/alarm-event.js') < html.index('/static/app.js')
    assert 'showAlarmExplanation();' in script
    assert 'onAlarmCanvasClick(event,canvas' in script
    assert 'UI effects on' in theme and 'UI effects off' in theme
    assert 'waveform replay unaffected' in theme.lower()


def test_wfdb_header_data_explained_and_old_patient_data_not_uploaded():
    html=(WEB/'index.html').read_text(encoding='utf-8')
    assert 'matching <strong>.hea and .dat together</strong>' in html
    assert 'id="datasetFiles"' in html
    assert 'importWFDBFiles' in html


def test_alarm_explanation_asset_served(client):
    r=client.get('/static/alarm-event.js')
    assert r.status_code==200
    assert 'No live monitor audio' in r.text
    assert r.headers['x-content-type-options']=='nosniff'


def test_node_reference_examples():
    node=shutil.which('node')
    if node is None:
        pytest.skip('Node not installed: browser JS examples are verified in CI')
    result=subprocess.run([node, str(Path(__file__).with_name('alarm-event14.cjs'))],
        capture_output=True,text=True,timeout=15,check=False)
    assert result.returncode==0, result.stderr
    assert '6 provenance-driven' in result.stdout
