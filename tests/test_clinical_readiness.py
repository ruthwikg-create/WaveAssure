from pathlib import Path
from scripts.clinical_readiness_audit import audit,markdown

ROOT=Path(__file__).resolve().parents[1]

def test_real_source_does_not_claim_hospital_authorization():
    status=audit(ROOT)
    assert status['release_decision']=='BLOCKED_FOR_CLINICAL_USE'
    assert status['permissions_granted'] is False
    assert 'NOT APPROVED' in markdown(status)
    assert status['model_artifact_status']=='ABSENT'


def test_fake_model_file_never_confers_authority(tmp_path):
    folder=tmp_path/'models'/'vtac'
    folder.mkdir(parents=True)
    (folder/'vt_model.json').write_text('{"fake":true}',encoding='utf-8')
    status=audit(tmp_path)
    assert status['release_decision']=='BLOCKED_FOR_CLINICAL_USE'
    assert status['model_artifact_status']=='PRESENT_UNVERIFIED'
    assert not status['permissions_granted']
