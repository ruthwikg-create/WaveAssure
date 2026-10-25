"""Wide ECG matrix preview regressions; synthetic data and source contracts only."""
import shutil
import subprocess
from pathlib import Path
import pytest
from waveassure.schemas import CSVImport
from waveassure.csv_input import parse_csv

ROOT=Path(__file__).resolve().parents[1]


def test_matrix_preview_is_not_reinterpreted_as_continuous_ecg():
    """Existing API must continue to reject missing elapsed-time headers."""
    names=[str(i) for i in range(140)]+['label']
    rows=[','.join(['0.2']*140+['1']) for _ in range(120)]
    csv_text=','.join(names)+'\n'+'\n'.join(rows)
    with pytest.raises(ValueError,match='Unsupported columns'):
        parse_csv(CSVImport(title='matrix not clinical',
                            csv_text=csv_text))


@pytest.mark.skipif(shutil.which('node') is None,reason='Node unavailable; CI checks Node')
def test_ecg_matrix_segment_preview_node_contract():
    r=subprocess.run(['node',str(ROOT/'tests'/'ecg-matrix17.cjs')],
                     capture_output=True,text=True,timeout=20)
    assert r.returncode==0,r.stderr
    assert 'PASS' in r.stdout


def test_wide_ecg_upload_is_not_mapped_to_unsupported_sample_rate():
    app=(ROOT/'web'/'app.js').read_text(encoding='utf-8')
    html=(ROOT/'web'/'index.html').read_text(encoding='utf-8')
    assert 'WaveAssureECGMatrix.inspect(head)' in app
    assert 'WaveAssureECGPreview.show(file,matrix)' in app
    assert 'Nothing is sent to the WaveAssure API in this preview.' in html
    assert '/api/import-csv' in app  # original actual recording importer is still separate
