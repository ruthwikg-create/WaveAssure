"""Conservative engineering status audit; NEVER grants regulatory or clinical approval.

No self-attested file can change external-approval status. Refer signed evidence
and approvals to an independent assessor and the proper authority.
"""
from __future__ import annotations
import argparse
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def audit(root: Path) -> dict:
    root = Path(root)
    api_path = root / 'waveassure' / 'api.py'
    api = api_path.read_text(encoding='utf-8') if api_path.exists() else ''
    model = root / 'models' / 'vtac' / 'vt_model.json'
    metrics = root / 'models' / 'vtac' / 'metrics.json'
    model_status = 'ABSENT'
    if model.exists():
        model_status = 'PRESENT_UNVERIFIED' # never certify merely by file existence
    checkpoints = [
        ('INTENDED_USE', 'Research-only intended use specified', (root/'docs'/'INTENDED_USE.md').is_file(), 'internal documentation only'),
        ('RISK_REGISTER', 'Preliminary hazards recorded', (root/'docs'/'HAZARD_REGISTER.csv').is_file(), 'not a completed ISO 14971 risk management file'),
        ('REQUIREMENTS', 'Preliminary requirements traceability', (root/'docs'/'REQUIREMENTS_TRACEABILITY.csv').is_file(), 'not signed-off complete traceability'),
        ('LOCAL_BOUNDARY', 'Local-only request filter present', 'local_only_security' in api and '_is_loopback' in api, 'not suitable for hospital network'),
        ('LIVE_ALARM_CONTROL', 'No live bedside alarm control', 'alarm_control' in api and "'none'" in api, 'not a validated system-level guarantee'),
        ('MODEL_ARTIFACT', 'Local model artifact present', model.exists(), model_status),
        ('MODEL_RESULTS', 'Local metrics file present', metrics.exists(), 'unverified provenance and performance even if file is present'),
        ('MODEL_ATTESTATION_GUARD', 'Pinned research model signature guard exists', (root/'docs'/'MODEL_ARTIFACT_TRUST.md').is_file() and 'verify_model_attestation' in (root/'waveassure'/'alarm_model.py').read_text(encoding='utf-8'), 'engineering-only check; cannot prove training authenticity or clinical approval'),
        ('REVIEW_MODE_GUARD', 'Separate research review route isolation exists', 'WAVEASSURE_WORKSPACE_MODE' in api and 'WAVEASSURE_REVIEW_KEY' in api, 'research-mode restriction only; not hospital RBAC or clinical blinding'),
        ('MULTIUSER_AUTH', 'Hospital-grade authentication and authorization assessed', False, 'missing dedicated authenticated accounts, roles, access reviews'),
        ('PHI_GOVERNANCE', 'Patient-data safeguards audited', False, 'no certified privacy controls, DPA, validated de-identification, retention policy'),
        ('INDEPENDENT_BLINDING', 'Independent blinded clinical review verified', False, 'reference labels accessible through engineering API'),
        ('VALIDATED_AI', 'External and independent clinical validation signed', False, 'unperformed; no real-data held-out results independently verified'),
        ('QMS_AUDIT', 'Manufacturer QMS independently audited', False, 'no organization-wide certified QMS'),
        ('PRODUCT_STANDARDS', 'Applicable standards independently assessed', False, 'no accredited conformity assessment available'),
        ('SITE_ETHICS', 'Institutional Ethics Committee approval for specific study verified', False, 'no signed approval submitted or independently confirmed'),
        ('CDSCO_PERMISSION', 'Applicable regulator permissions verified', False, 'risk class and applicability require regulatory determination'),
        ('HOSPITAL_AGREEMENT', 'Hospital sponsor/PI/site data agreement verified', False, 'no hospital sponsor, PI or site agreement'),
        ('CYBERSECURITY', 'Penetration, threat model and software update lifecycle independently audited', False, 'not independently assessed'),
    ]
    entries = [dict(id=i, requirement=desc, evidence_present=bool(ok), limitation=lim) for i,desc,ok,lim in checkpoints]
    all_critical_met = all(x['evidence_present'] for x in entries)
    return dict(
        generated_at=datetime.now(timezone.utc).isoformat(),
        scope='Source-level engineering readiness review only',
        model_artifact_status=model_status,
        model_file_sha256=hashlib.sha256(model.read_bytes()).hexdigest() if model.exists() else None,
        gates=entries,
        gate_summary={'completed_provisional_checks':sum(e['evidence_present'] for e in entries), 'total_checks':len(entries)},
        release_decision='BLOCKED_FOR_CLINICAL_USE' if not all_critical_met else 'REQUIRES_INDEPENDENT_ASSESSMENT',
        permissions_granted=False,
        approval_evidence='None independently verified',
        caution='The tool cannot determine legal classification, validate a model, certify standards, or grant hospital permission.'
    )


def markdown(result: dict) -> str:
    lines=['# WaveAssure Clinical and Regulatory Readiness — NOT APPROVED','',
        '**Decision: '+result['release_decision']+'**','',
        'This is a **development self-audit**, not regulatory advice or independent certification.','',
        '| Gate | Internal evidence? | What remains |','|---|---|---|']
    for entry in result['gates']:
        lines.append('| '+entry['requirement'].replace('|','/')+' | '+('partial only' if entry['evidence_present'] else 'no')+' | '+entry['limitation'].replace('|','/')+' |')
    lines += ['', '## Approval status', '',
        '- **Device risk class:** NOT DETERMINED BY CDSCO',
        '- **Real-data trained classifier and accuracy:** NOT INDEPENDENTLY VERIFIED',
        '- **IEC/ISO compliance:** NOT ESTABLISHED',
        '- **ISO 13485 certificate:** NOT HELD',
        '- **Clinical investigation permission:** NOT VERIFIED',
        '- **Ethics approval for a named study:** NOT VERIFIED',
        '- **Hospital patient-care use:** NOT AUTHORIZED', '',
        'See `regulatory/INDIA_APPROVAL_PATHWAY.md` for the staged approval path.','']
    return '\n'.join(lines)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--output', type=Path, default=ROOT/'reports'/'CLINICAL_READINESS.md')
    p.add_argument('--strict', action='store_true',help='Exit with code 2 while not independently cleared')
    args=p.parse_args(argv)
    report=audit(args.root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(markdown(report),encoding='utf-8')
    args.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'decision':report['release_decision'],'report':str(args.output)},indent=2))
    return 2 if args.strict else 0

if __name__=='__main__':
    raise SystemExit(main())
