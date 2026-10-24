# WaveAssure v0.10.0 — Reproducible Engineering Verification

**Date:** 24 October 2026  
**Scope:** research-only local software; no patients, medical-device approval or clinical performance measurements.

## Tests reproduced in this execution environment

- `python -m pytest -q` — **83 passed**; Python test fixtures are synthetic / artificial.
- `python -m compileall -q waveassure scripts benchmarks` — **passed**.
- `node --check web/app.js` and `node --check web/review.js` — **passed**.
- Chromium DOM automation with **an in-process FastAPI TestClient transport replacing actual network requests** — selected flows completed without JavaScript exceptions:
  - Workbench initial state, create deterministic synthetic record, display three waveforms.
  - Inject dropout into an artificial record, preserve source; records list and audit view update.
  - Review practice correctly refuses a pilot when no 300-second research record is available.
  - Dedicated reviewer mode with two **artificial labelled fixtures**: create session, view waveform, submit both assessments, finalize and make report export available.
- Browser-to-localhost or deployed web-server navigation **was restricted by this execution environment**; **no real network browser end-to-end test or Windows acceptance test was performed**.
- `python scripts/clinical_readiness_audit.py --strict` — **expected exit code 2**, decision `BLOCKED_FOR_CLINICAL_USE`.

## Fixes exercised in tests

1. Corrupted compressed record bytes and altered record metadata fail with controlled HTTP 409.
2. Writes cannot continue when the local audit chain has been tampered with.
3. New reviewer sessions pin each original case payload hash. Review, finalization and export reject changed sources.
4. UI prevents older asynchronous record/window responses from overwriting a newer selection; fault-derived records are visibly labelled.
5. Windows launcher sets its operating mode explicitly; CI additionally checks JavaScript syntax.

## Important limits

This is **developer verification**, not independent design-control verification. Local audit hashes have no independent anchor; a privileged administrator can rewrite the whole history. The signer for models provides integrity custody, not medical-data training proof. No real-data-trained VT classifier, clinical performance metrics, representative-user usability study, quality-system audit, independent penetration test, ethics approval, CDSCO permission or hospital authorization was demonstrated.

**Release recommendation:** use only for authorized offline synthetic/de-identified research and education. **Reject for patient-care, real-time monitoring, diagnosis, alarm suppression and formal clinical trials without further evidence and permissions.**
