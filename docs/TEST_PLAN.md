# Research software verification plan

**Scope:** Basic unit, integration, API, and optional browser smoke testing through v0.5.0. These are not medical device acceptance or clinical validation tests.

## Core verification
1. Install only free Python dependencies and run `python -m pytest -v`.
2. Verify health endpoint returns `live_monitoring:false`, and UI contains research warnings.
3. Verify deterministic baseline/fast rhythm/artifact demos; repeat baseline and compare sample values.
4. Verify invalid units, mismatched signals, nonfinite numeric data, duplicate/irregular timestamps and unsupported identifier columns are rejected.
5. Verify fault injection preserves parent record, reports changed QC and generates a unique child.
6. Verify report includes payload checksum, analysis, model availability and disclaimers.
7. Verify local audit chain intact, then alter a test event and confirm check fails.
8. Verify benchmark metadata joins by record+event and refuses patient overlap between official splits.

## Acceptance criteria for v0.1
All automated tests pass without skipped safety tests; source code visible; no clinical claim; no remote binding; research-only banner; optional model benchmark not falsely shown as evaluated. Failures block the release and must be documented.

## Later verification (NOT complete)
- Integration benchmark with downloaded VTaC; one-time untouched test evaluation.
- Statistical uncertainty, confidence intervals and external validation on a distinct dataset.
- Threat assessment, penetration testing, usability study, verification independence.
- Datasets, hardware calibrators and formal standards purchased/licensed as applicable.


## v0.5 release regression scope

- Reject off-loopback clients, unexpected HTTP Host headers, cross-origin requests and large declared request bodies.
- Keep user-supplied synthetic records from claiming expert labels.
- Verify optional version-matched PhysioNet SHA256SUMS paths and content and reject path traversal.
- Reject duplicate event IDs and patient-record overlap across data partitions in direct model training.
- Run `pytest --junitxml=reports/junit-v0.5.xml` before publication audit.

**Remaining:** No formal independent V&V review; no live physiological monitor verification; Windows device acceptance not executed in this environment; browser E2E release acceptance should be repeated on a Windows machine.
