# WaveAssure v0.9.0 — Corrective engineering action report

**Review authority:** Self-assessed AI-assisted engineering work; NOT an independent assessor, hospital board, clinical investigator, accreditation body or medical regulator. **Patient-care decision: REJECT / BLOCKED.**

## Directly observed nonconformities

| ID | Defect in v0.8.0 | Corrective code change in v0.9.0 | Actual verification here | Status |
|---|---|---|---|---|
| S-02 | Self-hashed model with no training evidence accepted | Runtime now requires an installation-pinned external Ed25519 attestation | Forged self-hash rejected; tampered signed model rejected; changed signer identity rejected; wrong key rejected; smoke-test model rejected | **Engineering mitigation verified on synthetic fixtures; actual provenance not established** |
| S-03 | Reviewer route hides reference label but engineering API exposes it | Dedicated reviewer process denies engineering routes; reviewer key required for pilot routes | Forged direct GET of record returns 403, unauthenticated reviewer GET returns 401, export unavailable until finalize | **Local route-isolation verified; independent blinded study NOT demonstrated** |
| Reliability: corrupt records | Some record-access endpoints surfaced uncaught integrity errors | Caught tampering errors and returned HTTP 409 | Tampered SQLite source returned HTTP 409 for multiple endpoints | **Limited local tests passed; independent V&V pending** |
| Reliability: preview defaults | Preview route accidentally required query parameters | Defined safe start/window query defaults | Default preview route exercised in tampering test | **Unit-level fix verified** |
| Output control | Model can score excessive missing primary ECG evidence | Added explicit engineering abstain condition in API inference | Missing primary features and >20% missingness rejected in adversarial tests | **Prototype heuristic only; threshold not analytically or clinically validated** |

## Eight broad medical-device release gates — re-evaluation

| Gate | Current status | Needed to close |
|---|---|---|
| Clinical model performance | **FAIL** | Genuine True/False training data, locked model and independently reviewed held-out and external performance |
| Patient safety | **FAIL** | Full ISO 14971 risk process and verified, clinically justified residual-risk controls |
| Security | **FAIL** | Patient-data governance, hospital authentication, independent penetration testing, protected audit and secure deployment |
| Software reliability | **PARTIAL** | Independent V&V, calibrated measurements, traceability, platform/device/recovery testing and system acceptance |
| Usability | **NOT DEMONSTRATED** | Planned and evaluated usability validation with representative end users, ethics as applicable |
| Quality management | **NOT DEMONSTRATED** | Manufacturer QMS, records, internal audits and assessment/certification as applicable |
| Ethics and regulatory approval | **NOT OBTAINED** | Relevant institutional ethics committee and CDSCO determination/permissions; cannot be issued by a developer |
| Hospital site acceptance | **NOT OBTAINED** | Hospital authorized review, IT controls, SOPs, installation and site acceptance testing |

## Verification scope

Automated regression and adverse-path tests use artificial code-generated files and no patient data. Tests executed in the Linux container only; GitHub Windows CI is **configured but has not been run in this environment**. No real VTaC model trained or genuine clinical performance measured. A test count is not a medical approval metric.

**Do not present this release as hospital-ready or independently clinically blinded.**
