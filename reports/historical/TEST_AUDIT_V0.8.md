# WaveAssure v0.8.0 — Executed engineering checks
Date: 24 October 2026.

- `python -m pytest -q --junitxml=reports/junit-v0.8.xml`: **65 passed** in the local container environment (Python runtime here; NOT user Windows host).
- `python -m compileall -q waveassure scripts benchmarks`: passed.
- `python scripts/publication_audit.py`: software research-release candidate; research-results publication blocked.
- `python scripts/clinical_readiness_audit.py`: **BLOCKED_FOR_CLINICAL_USE**, as expected.
- FastAPI in-process TestClient smoke: GET `/api/health` returns HTTP 200 with `research_only`; model status reports NOT TRAINED; disallowed Host returns HTTP 403.
- No patient data or trained clinical model present in deliverable.
- No successful formal Windows-specific site qualification, independently validated human factors, cross-platform real-device tests, third-party penetration test, ISO 13485 audit, IEC/ISO conformity assessment, or CDSCO/hospital authorization has been performed.
- Model study: NOT RUN on genuine full labelled VTaC dataset; no clinical sensitivity/specificity or trial outcome computed.

Test report evidence: `reports/junit-v0.8.xml` and `reports/CLINICAL_READINESS.json`.

This is an **internal software-verification record**, not a proof of patient safety or clinical performance. Existing tests have unit and internal API scope; data accuracy and safety claims require separate formal V&V.
