"""Research printable report layout and ephemeral metadata regressions."""
from pathlib import Path
import shutil
import subprocess
from waveassure.report_html import report_html
from waveassure.evidence import create_evidence
from waveassure.signals import demo_record

ROOT=Path(__file__).resolve().parents[1]


def _report():
    record=demo_record('baseline')
    meta={'id':'abcd1234','title':record.title,'origin':record.origin,
          'data_sha256':'e1'*32,'fault':None,'parent_id':None}
    return create_evidence(record,meta,{'ok':True})


def test_patient_editor_above_printable_evidence_with_safe_placeholders():
    html=report_html(_report())
    for control in ('studyLabel','studyId','age','sex','unit','recordedOn','reviewer','reviewerNotes'):
        assert 'id="'+control+'"' in html
        assert 'data-patient="'+control+'"' in html
    assert html.index('id="studyLabel"') < html.index('id="printableEvidence"')
    assert 'Not provided' in html
    assert '/static/report-editor.js' in html
    assert 'autocomplete="off"' in html
    assert 'Do not enter real names' in html
    assert 'RESEARCH USE ONLY' in html


def test_report_has_record_traceability_without_unnecessary_clinical_claims():
    html=report_html(_report())
    for heading in ('Patient / research details','Recording details','Event summary',
                    'Signal evidence','Record traceability'):
        assert heading in html
    assert 'SYNTHETIC' in html
    assert 'No documented alarm reference' in html
    assert 'No medical decision provided' in html
    assert 'No alarm event was established' in html
    assert 'Data SHA-256:' in html
    assert 'Not independently verified' in html
    assert 'Rapid ventricular rhythm' not in html
    assert 'Normal sinus rhythm' not in html


def test_print_css_and_no_external_report_editor_requests(client):
    page=client.get('/static/report.css')
    assert page.status_code==200
    assert '@page{size:A4 portrait' in page.text
    assert '.no-print{display:none!important}' in page.text
    script=client.get('/static/report-editor.js')
    assert script.status_code==200
    assert 'window.print()' in script.text
    assert 'target.textContent' in script.text
    for forbidden in ('fetch(', 'localStorage', 'sessionStorage', 'XMLHttpRequest', 'sendBeacon'):
        assert forbidden not in script.text


def test_print_preview_route(client):
    rid=client.post('/api/demo?kind=baseline').json()['id']
    page=client.get(f'/api/records/{rid}/report.html')
    assert page.status_code==200
    assert page.text.index('id="details-heading"')<page.text.index('id="printableEvidence"')
    assert 'Save as PDF' in page.text


def test_javascript_editor_behavior_with_dom_stub():
    if not shutil.which('node'):
        return
    run=subprocess.run(['node',str(ROOT/'tests'/'report-editor22.cjs')],
                       capture_output=True,text=True,timeout=12)
    assert run.returncode==0,run.stderr
    assert 'PASS' in run.stdout
