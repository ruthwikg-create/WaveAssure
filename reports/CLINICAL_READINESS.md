# WaveAssure Clinical and Regulatory Readiness — NOT APPROVED

**Decision: BLOCKED_FOR_CLINICAL_USE**

This is a **development self-audit**, not regulatory advice or independent certification.

| Gate | Internal evidence? | What remains |
|---|---|---|
| Research-only intended use specified | partial only | internal documentation only |
| Preliminary hazards recorded | partial only | not a completed ISO 14971 risk management file |
| Preliminary requirements traceability | partial only | not signed-off complete traceability |
| Local-only request filter present | partial only | not suitable for hospital network |
| No live bedside alarm control | partial only | not a validated system-level guarantee |
| Local model artifact present | no | ABSENT |
| Local metrics file present | no | unverified provenance and performance even if file is present |
| Pinned research model signature guard exists | partial only | engineering-only check; cannot prove training authenticity or clinical approval |
| Separate research review route isolation exists | partial only | research-mode restriction only; not hospital RBAC or clinical blinding |
| Hospital-grade authentication and authorization assessed | no | missing dedicated authenticated accounts, roles, access reviews |
| Patient-data safeguards audited | no | no certified privacy controls, DPA, validated de-identification, retention policy |
| Independent blinded clinical review verified | no | reference labels accessible through engineering API |
| External and independent clinical validation signed | no | unperformed; no real-data held-out results independently verified |
| Manufacturer QMS independently audited | no | no organization-wide certified QMS |
| Applicable standards independently assessed | no | no accredited conformity assessment available |
| Institutional Ethics Committee approval for specific study verified | no | no signed approval submitted or independently confirmed |
| Applicable regulator permissions verified | no | risk class and applicability require regulatory determination |
| Hospital sponsor/PI/site data agreement verified | no | no hospital sponsor, PI or site agreement |
| Penetration, threat model and software update lifecycle independently audited | no | not independently assessed |

## Approval status

- **Device risk class:** NOT DETERMINED BY CDSCO
- **Real-data trained classifier and accuracy:** NOT INDEPENDENTLY VERIFIED
- **IEC/ISO compliance:** NOT ESTABLISHED
- **ISO 13485 certificate:** NOT HELD
- **Clinical investigation permission:** NOT VERIFIED
- **Ethics approval for a named study:** NOT VERIFIED
- **Hospital patient-care use:** NOT AUTHORIZED

See `regulatory/INDIA_APPROVAL_PATHWAY.md` for the staged approval path.
