# Clinical evaluation and investigator study plan — WORKING TEMPLATE ONLY
**NOT APPROVED. Do not recruit participants, extract new hospital data, install in a hospital or run prospective observation under this template. Obtain sponsor, clinical PI, Ethics Committee and applicable regulatory review first.**

## Proposed stages and gates
**Stage A — software analytical bench validation (no patient participation):** locked unit tests; public, authorized de-identified archival data; documented checksum/provenance, lead calibration cross-checks; complete and incomplete input cases; model training and independently held-out evaluation. No patient contact. Do not label as clinical trial.

**Stage B — retrospective clinical record study:** protocol review and written determination/approval by site Ethics Committee, rights/consent/waiver determination, institutional Data Use Agreement, clinician annotation charter, locked labels, independent blinding, adjudication and sample-size justification. Hospital datasets must be controlled in a secure, access-logged research environment—not the current unauthenticated app.

**Stage C — prospective silent observation (only after approvals):** no display of AI conclusions to treating staff, no influence on alarms, no interconnection controlling patient monitors, clinical risk management review, formal ethics and CDSCO determination for investigational medical software. Emergency stopping rules, PI oversight, adverse event reporting plan and traceability required.

**Stage D — clinical performance/utility investigation as needed:** formal regulatory pathway decided by sponsor and CDSCO, prespecified patient-safety endpoints, validated integration, monitored ethics/regulatory oversight and licensed manufacturer controls.

## Fields that must be filled before any formal hospital study
- Sponsor legal entity / quality owner / principal investigator / institution: **NOT APPOINTED**
- Exact clinical intended use and risk classification: **NOT FINALIZED / NOT CONFIRMED BY CDSCO**
- Target patients, monitor models, channel quality, alarm definition: **TO BE SPECIFIED**
- Exclusions and per-patient/per-site split rules: **TO BE SPECIFIED**
- Reference standard: **independent expert annotation; detailed adjudication protocol REQUIRED**
- Primary endpoint: **TO BE AGREED WITH CLINICAL PI**, e.g. sensitivity for true VT alarm events at a predeclared operating point. False-negative performance must be explicitly analysed.
- Secondary endpoints: false-alarm reduction as an offline retrospective measure, specificity, precision, AUROC, confidence intervals, calibration, abstention, artifact performance, stratification by hospital/device/patient group.
- Sample size / power justification: **NOT CALCULATED**; avoid invented case counts or accuracy targets.
- Model freeze, algorithm version, thresholds and statistical plan: **NOT APPROVED**
- Bias/subgroup analysis, missing channels and out-of-distribution rules: **NOT IMPLEMENTED/VALIDATED**
- Privacy controls, consent/waiver, encrypted storage, access restriction and key custody: **NOT IMPLEMENTED**
- Monitoring, case-report form, adverse event definition, escalation, discontinuation and safety review: **NOT APPROVED**
- Hospital EC determination/approval ID: **NONE**
- Applicable CDSCO permission / form: **NONE**
- CTRI number if applicable: **NONE**

## Predeclared stop/go criteria
- Abort when waveform integrity cannot be verified or provenance is unknown.
- Flag uncalibrated, missing, or incorrectly mapped leads; show "cannot assess" rather than medical outputs.
- No progression to patient-facing use on the basis of internal accuracy figures alone.
- Any participant/hospital study requires qualified PI oversight, site approval, ethics review and appropriate permissions.
