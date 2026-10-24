# WaveAssure v0.8 — Source-based gap report (24 October 2026)
**Review method:** inspected code, unit/integration test suite and documentation, and compared regulatory topics with CDSCO guidance. Not an independent accredited audit, penetration test, validation study or certification.

## What has been checked directly
- `pytest` automated suite on this source: see `reports/historical/TEST_AUDIT_V0.8.md`; test suite does NOT cover all expected hospital workflows.
- FastAPI app binds locally when started via packaged Windows script and has request source/host filtering.
- SQL storage uses a local SQLite file with a hash-linked audit ledger; the ledger is not cryptographically signed, immutable or independent.
- Retrospective pilot stores reviewer decisions; reference labels can be obtained through other engineering API routes, so **not independently blinded**.
- WFDB import supports only a restricted waveform format; clinical device integrations, patient monitor protocols, and different hardware calibration conditions are NOT validated.
- Clinical VT model file not shipped; no clinical sensitivity/specificity or externally verified trial results.

## Critical blockers for use in hospitals or labs as a medical product
| ID | Finding | Consequence | Required closure |
|---|---|---|---|
| BLK-01 | No independently verified True/False VT model or held-out external validation | Serious VT may be missed, false VT risk | Obtain sufficient labelled data, independent site/subject-separated evaluation with predeclared criteria, sensitivity CIs and locked model |
| BLK-02 | No organization-wide controlled medical QMS | Development/release not traceable to a regulated manufacturer | Responsible legal entity and implemented/audited ISO 13485 QMS |
| BLK-03 | No complete risk-management file, residual risk analysis or formal hazard control verification | Unassessed foreseeable patient harm | ISO 14971 full lifecycle risk management, clinical review, traceability |
| BLK-04 | No authenticated multiuser permissions, protected PHI vault, validated privacy management or verified identity | Patient data, reviewers and reports may be exposed/altered | Design and independently test hospital authorization, encryption, retention, backups, incident management; privacy review |
| BLK-05 | Reviewer label masking only via some routes | Bias/leakage invalidates blinded reviewer study | Independent server-side blinding and access segregation; audited investigator roles |
| BLK-06 | No device integration protocol certification, hazard analysis for alarms, security assessment or fail-safe fallback | Incorrect readings or clinical actions | Controlled interface specifications, real-device test plans, hazard handling, IEC 60601 applicability assessment |
| BLK-07 | No signed clinical protocol, appointed PI, ethics review, CDSCO classification/permissions or study registrations | Unlawful or unethical investigation may occur | Sponsor/regulatory officer/clinical PI; obtain site and regulator approvals before study |
| BLK-08 | Unit tests only, no independent formal V&V, cross-platform acceptance, usability study, software SBOM assessment, failover/recovery tests | Could fail in real workflow despite green test suite | Evidence-based V&V, IEC 62304 lifecycle plan, usability, security, reliability and configuration validation |
| BLK-09 | Local computer database and non-signed exports lack controlled custody | Research evidence integrity not adequate for regulated trial | Validated controlled data capture, independent audit trail, archival/access policy, EDC/quality processes |

## What can be claimed
- **Research prototype:** yes; usable for offline engineering exploration with permitted de-identified/synthetic records.
- **Internal automated tests passing:** yes if fresh `pytest` result reproduces.
- **Clinically validated algorithm:** NO.
- **Validated medical safety or medical grade:** NO.
- **ISO/IEC certified/conformant:** NO.
- **CDSCO/hospital clinical-trial permission:** NO.
- **Ready for patient care/hospital operations:** NO.

## Risk priority
Immediate: formal intended-use freeze, clinical sponsor, regulatory scoping and ethics determination. Engineering next: completed benchmark data, input calibration, data governance, audit design and risk-management system. Deployment readiness: independent validation, hazard acceptance, organizational QMS, clinical and regulatory approvals.
