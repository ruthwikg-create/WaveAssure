# WaveAssure 0.4.0 verification

- Genuine VTaC training **not run in this environment** because only a *user-held* verified True VT recording is known and neither original waveform files nor the official split CSV are available here.
- 36 automated tests passed in this build environment (Python 3.13) using synthetic fixtures.
- Regression and research training software tests use synthetic fixtures for engineering checks, **not patient data** and not evidence of medical accuracy.
- Dataset acquisition uses sequential official HTTPS requests with range-resume support and verifies supported WFDB checksums before training.
- Threshold selection uses only validation, not test data; test set is scored after fitting.
- No real-world Windows runtime, clinical, regulatory, or external validation is claimed.
