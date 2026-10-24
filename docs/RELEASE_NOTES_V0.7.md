# WaveAssure v0.7.0 — Evidence-First Research Release

### Implemented

- Added new deterministic evidence API `/api/records/{id}/evidence` and versioned research JSON download `/api/records/{id}/report`.
- Added a printable offline HTML research report at `/api/records/{id}/report.html` for reviewer inspection (print from browser with Ctrl+P).
- Added original source, dataset reference annotation, measurement method, exact sample windows, missing/finite counts, SHA-256 payload integrity, unsigned audit state, and explicit evidence limitations.
- Added user interface summary of actual input provenance and exact descriptive 30 s pre-alarm measurements.
- Changed ambiguous "QC passed" text to "No flags" for unvalidated heuristic checks; suppressed unvalidated ECG-rate estimate display on genuine WFDB recordings.
- Fixed a high-risk data-label bug: fault-derived waveforms do not inherit the source event's True/False reference label.
- Distinguished source waveform vs derived fault data classes.
- Added output contract / verification documentation and regression tests.

### Not implemented

A trained VT model, external validation, actual VTaC performance results, clinical decision support, manufacturer alarm conformance, regulatory clearance, encryption, strong identity/access controls, hospital deployment, independent safety evaluation, or any clinical trial. **This release must not be used for patient care or real-time alarm decisions.**

### Verification

Automated software regression suite and a JavaScript syntax check ran successfully in the build container. Backend HTML/JSON routes are covered by API tests. Headless browser access to localhost is blocked in this environment, so **Windows browser visual acceptance remains unverified**.
