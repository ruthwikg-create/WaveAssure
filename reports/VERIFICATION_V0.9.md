# WaveAssure v0.9.0 — Local test execution evidence

**Scope:** Only source + synthetic biomedical fixtures available in this execution environment. **No patient files were accessible.**

Executed in the local Linux Python environment:

```text
python -m pytest -q --junitxml=reports/junit-v0.9.xml
76 passed
python -m compileall -q waveassure benchmarks scripts
Exit 0
node --check web/review.js
Exit 0
node --check web/app.js
Exit 0
python scripts/clinical_readiness_audit.py --strict
BLOCKED_FOR_CLINICAL_USE; exit 2 (expected)
```

Full JUnit results are available in `reports/junit-v0.9.xml`. Targeted negative tests are in `tests/test_safety_hardening09.py` and use artificial fixtures only. The prior v0.8.0 regression tests also passed. No tests on the user's actual Windows installation, clinical equipment, source VTaC dataset, or hospital network were performed. GitHub Windows CI is **configured, not executed here**.

Additional finding during review: the printable HTML report embedded a `<style>` element incompatible with WaveAssure's own CSP. It now loads `/static/report.css` as a separate stylesheet and has a regression test.

**Passes in this report do not establish clinical-model performance, system cybersecurity, formal IEC/ISO conformity, or ethics/regulatory authorization.**
