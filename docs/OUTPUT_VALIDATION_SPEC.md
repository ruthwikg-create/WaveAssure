# WaveAssure 0.7 — Evidence Output Contract

**Status:** research-only software validation. This is not medical-device grade validation, a clinical report, or proof of conformity with ISO/IEC standards.

## Documented intended use
An offline tool for technicians and biomedical researchers to inspect de-identified historical WFDB/CSV waveforms, compute simple descriptive statistics, and generate software verification evidence. Not intended to monitor a living patient, screen for or diagnose arrhythmia, suppress an alarm, recommend care, replace a qualified professional, or support any time-critical decision.

## Source-of-truth categories

| Output element | Evidentiary origin | Permitted interpretation |
| --- | --- | --- |
| `sample_rate_hz`, `sample_count_per_channel`, `unit` | WFDB header or imported user schema | Description of input file, not verification of sensor calibration |
| `missing_samples`, `minimum`, `maximum`, `mean`, `standard_deviation` | Software computation over imported physical sample values | Descriptive arithmetic only, with raw missing values excluded from numeric statistics |
| `reference_annotation.label` | Official `event_labels.csv` *if available*, imported by the WFDB workflow | Dataset reference annotation about the alarm event, **not the application's inference** |
| `payload_sha256` | SHA-256 of the locally stored canonical record payload | Detects certain local changes, not source identity, external authenticity or signed evidence |
| `format_level_check_at_import` | On import, WFDB format-16 file size and digital-sample additive checksums | Bounded format-level data integrity, not PhysioNet SHA-256 provenance |
| `audit_chain_currently_valid` | Computed local SHA-256-linked SQLite audit chain | Not digitally signed or independent audit evidence |
| `clinical_alarm_assessment` | None | Explicitly **NOT PERFORMED** |
| `independent_true_false_vt_model_assessment` | Not in the evidence report | Model result must be separately obtained and documented after real training |

## Measurements algorithm `waveassure-window-statistics-v1`

- Use full recording, and on eligible **original** WFDB files with 300 s available, pre-alarm `[270,300)` and post-alarm `[300,330)` seconds. Do not use post-alarm values to make a pre-alarm predictive claim.
- Convert start/end seconds to sample index using `round(seconds * sampling_rate)`, clamp to available range, and preserve channel-specific `null` values as missing.
- Calculate total, valid and missing sample counts and missing fraction. Compute finite-value min/max/mean/median/population standard deviation. No interpolation for these statistics.
- Show units inherited from source and mark the absence of an independent calibration-accuracy assessment.
- Do not compute clinical thresholds, abnormality labels, disease risks, automated diagnoses, or nurse-notification priorities.
- For a fault-derived record, **do not inherit** the original dataset's reference label. Even when recording provenance remains visible, annotation must become `Unlabeled`.
- Numeric rounding is for display; this is not a measurement uncertainty assessment.

## Release gates

- Fail if source records are mutable without trace, imports accept invalid units, or a derived fault claims its parent's reference label.
- Fail if JSON or HTML report suggests an independent clinical diagnosis when the model has not been validated.
- Fail if a model presents unverified metrics as clinical sensitivity/specificity.
- Tests must verify the report endpoints, synthetic-data labelling, 300-second window boundaries, all-missing window behaviour, and escaping of HTML report fields.
- A 0.7 automated test pass is only a **software test pass**; it does not make a study, algorithm, or medical output clinically valid.

## Before even considering a clinical pilot

Requirements approved by a responsible clinical sponsor, documented regulatory and ethics determinations, representative de-identified real-world datasets, clinical reference standard and adjudication protocol, locked evaluation design, independently verified labels, statistical sample-size analysis, validated performance targets, quality-system controls, human-factors study, cybersecurity testing, credentialed reviewer procedures, and clinical/risk oversight.

Further reference: [FDA Clinical Decision Support final guidance, Jan 2026](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software); [IMDRF GMLP principles](https://www.imdrf.org/documents/good-machine-learning-practice-medical-device-development-guiding-principles); [ISO 14971:2019](https://www.iso.org/standard/72704.html).
