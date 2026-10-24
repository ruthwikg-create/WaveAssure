"""Generate a conservative, reproducible publication-readiness status report.

This does not approve clinical use or certify compliance with IEC/ISO standards.
No data are downloaded and model metrics are never invented.
"""
from __future__ import annotations
import argparse
import json
import hashlib
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent


def audit(root: Path) -> dict:
    required = ['README.md', 'LICENSE', 'CITATION.cff', 'CONTRIBUTING.md',
        'SECURITY.md', 'docs/INTENDED_USE.md', 'docs/HAZARD_REGISTER.csv',
        'docs/REQUIREMENTS_TRACEABILITY.csv', 'docs/STANDARDS_MATRIX.md',
        'publication/MANUSCRIPT_DRAFT.md', 'publication/REPORTING_CHECKLIST.md',
        'scripts/verify_dataset_sha256.py', '.github/workflows/tests.yml']
    missing = [x for x in required if not (root / x).is_file()]
    junit = root / 'reports' / 'junit-v0.9.xml'
    test_results = {'available': False}
    if junit.is_file():
        x = ET.parse(junit).getroot()
        suites = [x] if x.tag == 'testsuite' else list(x.findall('testsuite'))
        test_results = {'available': True,
            'tests': sum(int(v.attrib.get('tests', 0)) for v in suites),
            'failures': sum(int(v.attrib.get('failures', 0)) for v in suites),
            'errors': sum(int(v.attrib.get('errors', 0)) for v in suites),
            'skipped': sum(int(v.attrib.get('skipped', 0)) for v in suites),
            'evidence': 'reports/junit-v0.9.xml'}
    model = root / 'models' / 'vtac' / 'vt_model.json'
    metrics_path = root / 'models' / 'vtac' / 'metrics.json'
    metrics_evidence = {'trained_model_present': model.is_file(),
        'metrics_present': metrics_path.is_file(), 'genuine_research_results_verified': False}
    if metrics_path.is_file():
        try:
            raw = metrics_path.read_bytes()
            obj = json.loads(raw)
            metrics_evidence['metrics_sha256'] = hashlib.sha256(raw).hexdigest()
            metrics_evidence['declared_training_mode'] = obj.get('training_mode', 'missing')
            metrics_evidence['dataset_version'] = obj.get('data_version', 'unspecified')
            metrics_evidence['declared_test_metrics'] = obj.get('results', {}).get('test')
            metrics_evidence['comment'] = 'Self-reported local metrics; cannot establish genuine data provenance, clinical validity, or reproducibility independently.'
        except (ValueError, OSError):
            metrics_evidence['comment'] = 'Unparseable local metrics, cannot evaluate.'
    else:
        metrics_evidence['comment'] = 'No genuine model or held-out VTaC performance evidence bundled.'
    passed = (test_results['available'] and test_results['tests'] >= 1
              and test_results['failures'] == 0 and test_results['errors'] == 0)
    software_ready = not missing and passed
    return {
        'scope': 'open-source local research-software release (not clinical deployment)',
        'software_release_checklist': 'candidate_for_maintainer_review' if software_ready else 'blocked',
        'missing_files': missing,
        'automated_tests': test_results,
        'research_evidence': metrics_evidence,
        'clinical_use_approval': False,
        'clinical_accuracy_validated': False,
        'peer_review_completed': False,
        'manuscript_results_readiness': 'blocked_without_independent_real_data_evaluation',
        'standards_certified': False,
        'limitations': [
            'Passing software unit tests does not demonstrate medical efficacy.',
            'The baseline must be evaluated on adequate expert-labelled VTaC data.',
            'A small development subset is not a publishable clinical validation cohort.',
            'Independent prospective/multi-centre validation, approvals and controls remain unperformed.',
            'This source code is local only, has no multiuser authorization, TLS or clinical audit assurances.'
        ]
    }


def markdown(result: dict) -> str:
    t = result['automated_tests']
    return '\n'.join([
        '# WaveAssure publication readiness', '',
        '**Scope:** open-source local biomedical research software (not clinical use).',
        f"**Software release checklist:** {result['software_release_checklist']}",
        f"**Tests:** {t.get('tests', 'not run')} recorded; failures: {t.get('failures', 'unknown')}; errors: {t.get('errors','unknown')}",
        f"**Missing release files:** {', '.join(result['missing_files']) or 'None'}", '',
        '**Clinical accuracy validation:** NOT PERFORMED',
        '**Peer review:** NOT PERFORMED',
        '**Standards certification:** NOT CLAIMED',
        '**VTaC manuscript-results readiness:** BLOCKED pending real, adequate held-out evaluation.', '',
        '## Research evidence status', '',
        result['research_evidence'].get('comment', 'N/A'), '',
        '## Limitations', '',
        *['- ' + x for x in result['limitations']], '',
        'Generated by `scripts/publication_audit.py`; this is not an independent certification.', ''
    ])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT / 'reports' / 'PUBLICATION_READINESS.md')
    args = parser.parse_args(argv)
    result = audit(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown(result), encoding='utf-8')
    args.output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'software_release_checklist':result['software_release_checklist'],
        'research_manuscript':result['manuscript_results_readiness'],
        'report':str(args.output)}, indent=2))
    return 0 if result['software_release_checklist'] == 'candidate_for_maintainer_review' else 1

if __name__ == '__main__':
    sys.exit(main())
