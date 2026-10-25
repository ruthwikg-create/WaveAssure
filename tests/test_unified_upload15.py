"""Contract checks for the single research upload picker; not clinical testing."""
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class HTMLTree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inputs = []
        self.parents = []
        self.parents_of = {}
        self.void = {'meta','link','input','img','br','hr','source','area','base','embed','param','track','wbr'}

    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if attrs.get('id'):
            self.parents_of[attrs['id']] = tuple(self.parents)
        if tag == 'input' and attrs.get('type')=='file':
            self.inputs.append(attrs)
        if tag not in self.void:
            self.parents.append((tag,tuple(attrs.get('class','').split())))

    def handle_endtag(self, tag):
        if self.parents and self.parents[-1][0] == tag:
            self.parents.pop()


def test_only_one_visible_data_upload_input_and_correct_hierarchy():
    html=(WEB/'index.html').read_text(encoding='utf-8')
    p=HTMLTree();p.feed(html)
    assert len(p.inputs)==1
    f=p.inputs[0]
    assert f['id']=='datasetFiles'
    assert 'multiple' in f
    assert '.csv' in f['accept'] and '.hea' in f['accept'] and '.dat' in f['accept']
    assert ('div',('left-col',)) in p.parents_of['windowTools']
    assert ('div',('right-col',)) in p.parents_of['quality']
    assert '<summary>Already have a WFDB research dataset on this computer?' in html
    assert 'type="file"' not in html.replace('<input id="datasetFiles" type="file"','')


def test_selection_uses_unified_picker_and_provenance_preserved():
    script=(WEB/'app.js').read_text(encoding='utf-8')
    assert 'WaveAssureDatasetUpload.classify(files)' in script
    assert 'fileSelectionSequence' in script
    assert "$('datasetFiles').addEventListener('change'" in script
    assert "selectedCSV=null;selectedWFDB=null;" in script
    assert 'user_annotation_unverified' in (ROOT/'waveassure'/'wfdb_input.py').read_text(encoding='utf-8')
    assert 'id="wfdbHeader"' not in (WEB/'index.html').read_text(encoding='utf-8')


def test_node_picker_scenarios():
    node=shutil.which('node')
    if not node:pytest.skip('Node is unavailable locally (CI runs Node tests)')
    r=subprocess.run([node,str(ROOT/'tests'/'dataset-upload15.cjs')],capture_output=True,text=True,timeout=15)
    assert r.returncode==0,r.stderr
    assert '11 invalid selections' in r.stdout
