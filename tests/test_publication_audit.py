from scripts.publication_audit import audit, markdown


def test_audit_marks_missing_evidence_as_blocking(tmp_path):
    result = audit(tmp_path)
    assert result['software_release_checklist'] == 'blocked'
    assert result['clinical_accuracy_validated'] is False
    assert result['research_evidence']['genuine_research_results_verified'] is False
    assert 'BLOCKED' in markdown(result)


def test_existing_project_is_never_called_clinically_approved():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    result = audit(root)
    assert result['clinical_use_approval'] is False
    assert result['standards_certified'] is False
