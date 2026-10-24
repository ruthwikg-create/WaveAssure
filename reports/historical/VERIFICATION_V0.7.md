# WaveAssure v0.7.0 — Build verification evidence

Scope: research-grade descriptive signal-evidence workflow only, not clinical validation or medical-device verification and validation.

| Check | Recorded outcome | Meaning / qualification |
| --- | --- | --- |
| Automated Python tests | 63 passed; 0 failures; 0 errors | Local code-level checks with synthetic fixtures; not clinical evidence |
| HTML report route | 200, `text/html` | Endpoint returned in FastAPI TestClient; includes research-only banner |
| JSON report route | 200, `application/json` | Endpoint returned versioned evidence schema |
| Evidence API route | 200, `application/json` | Endpoint returns descriptive measurements and provenance |
| JavaScript parsing | `node --check web/app.js` passed | Syntax only, not full browser testing |
| Release readiness audit | `candidate_for_maintainer_review` | Developer checklist, not external release approval |
| Genuine VTaC model trained | **NO** | Dataset with both classes unavailable in this container |
| Clinical sensitivity/specificity | **NOT MEASURED** | No real held-out clinical evaluation executed |
| Browser visual acceptance | **NOT VERIFIED** | Chromium network policy blocked the localhost test |
| Regulatory and clinical approval | **NONE** | No IEC/ISO certification, CDSCO/FDA clearance or trial approval claimed |

Automated test JUnit source: `reports/junit-v0.7.xml`.

Critical regression: fault-derived recordings no longer inherit the source dataset's expert True/False reference label. Their technical data provenance is preserved while the derived annotation becomes `Unlabeled`.

Source code version: `waveassure/__init__.py` = 0.7.0. Re-run `scripts/check-release-windows.bat` on Windows and inspect app behavior with a de-identified original dataset file before using the software even as a clinician usability research prototype.
