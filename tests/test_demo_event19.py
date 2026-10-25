"""Synthetic-only demonstration marker regression contracts, not clinical validation."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.skipif(not shutil.which('node'),reason='Node absent; CI executes Node tests')
def test_synthetic_marker_provenance_and_hover_source():
    result=subprocess.run(['node',str(ROOT/'tests'/'demo-event19.cjs')],
                          capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    assert 'contracts PASS' in result.stdout


def test_demo_event_is_browser_only_and_never_persisted_in_record():
    app=(ROOT/'web'/'app.js').read_text(encoding='utf-8')
    code=(ROOT/'web'/'demo-event.js').read_text(encoding='utf-8')
    html=(ROOT/'web'/'index.html').read_text(encoding='utf-8')
    assert 'demoMarker={id:current.metadata.id,time}' in app
    assert 'current=loaded;demoMarker=null' in app
    assert "window.WaveAssureDemoEvent.explanation" in app
    assert 'Temporary browser-only demonstration marker' in code
    assert 'id="demoMarkerToggle"' in html
    assert 'alarm_time_s:rawAlarm' in app  # real user-supplied annotation remains separate
