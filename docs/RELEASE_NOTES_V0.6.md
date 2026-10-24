# WaveAssure v0.6.0 — verification release

## Added
- Offline clinician-review usability panel for previously imported and de-identified VTaC-format records.
- Per-reviewer pseudonymous sessions, case list snapshot, pre-alarm preview, decision with confidence and quality fields.
- Immutable submissions, hash-linked audit events, finalization, and JSON export after review completion.
- Explicit safeguards against making medical AI or clinical validation claims from data-unavailable runs.

## Verified
- All automated tests run from a local venv with synthetic fixtures only; no patient waveforms bundled.
- The browser UI is integrated but live browser automation was blocked by the test environment's localhost restriction; Windows browser acceptance testing remains pending.

## Known limitations
- **No trained VTaC True-vs-False model** distributed.
- **No IRB/IEC approval or clinical investigation authorization** supplied.
- Researcher workbench still exposes labels; pilot masking is not secure blinding.
- No authentication, TLS, legally recognized electronic signatures, data-governance/PHI handling, or professional validation.
- Do not deploy in a hospital, use for patient care, or claim regulated clinical standards conformance.
