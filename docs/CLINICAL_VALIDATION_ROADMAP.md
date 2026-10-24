# Research verification vs clinical validation

**No clinical validation has been performed.** WaveAssure must never be used to diagnose, treat, silence, filter, route, prioritize or replace real ICU alarms.

## Implemented research engineering safeguards

- Expert True/False labels, official patient/record-disjoint train/validation/test assignment
- WFDB length and per-channel checksum validation of simple shared format-16 waveforms
- Pre-alarm-only features; training-only medians/scaling; threshold selected from validation ONLY
- Held-out confusion matrix, sensitivity, specificity, precision, AUROC, AUPRC, Brier and descriptive Wilson 95% intervals (upon genuine training)
- Safe model JSON export and inference-parity tests; synthetic engineering smoke models disabled for app use

## Research evidence still needed

- Authenticated complete original waveforms with official SHA256SUMS from PhysioNet; current implementation checks WFDB additive checksums but not origin SHA256
- Larger patient-level expert-labelled cohort, repeated independent training and reproducible versioned run
- Patient-cluster-aware uncertainty analysis, subgroup performance, external-hospital/device validation and error-case reviews
- Clinician review and prospective *shadow-mode* evaluations conducted with appropriate approvals before clinical claims

**No claim of IEC 62304, IEC 60601-1-8, ISO 14971, ISO 13485 or regulatory certification.** Medical standards require comprehensive evidence, independent verification and review appropriate to intended use. This is software engineering practice inspired by relevant standards, not standards compliance certification.

VTaC source: https://physionet.org/content/vtac/1.1/
