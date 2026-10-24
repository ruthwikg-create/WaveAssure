# WaveAssure v0.3.0: verification summary

- 32 local automated tests passed in a Python 3.13 development container with NumPy, SciPy, scikit-learn, FastAPI and pytest.
- Node.js syntax check for the new frontend JavaScript passed.
- Automated research-model tests use **synthetic numeric software fixtures**, NOT authentic PhysioNet patient waveforms or validated alarm accuracy claims.
- Synthetic WFDB-format integration tests in the base suite exercised decoder checks for missing/corrupt files and API import.
- Test suite includes full-file shared format-16 sample checksum verification, and guards the 300-second onset window against future data leakage, rejects 1-class training, verifies tamper detection on the JSON model, and blocks engineering smoke models from being loaded by the application.
- The actual user waveform `623dd0_0023` is on the user's local `D:` drive and is **not available in this container**. It was previously reported as validated by an independent format-16 integrity script, but was not imported or used to train here.
- The full dataset's official split CSV was not obtained in this environment and a real full VTaC model **has not** been trained, externally benchmarked or clinically validated.
- The optional `wfdb` Python package was unavailable in this test container; full PhysioNet WFDB training cannot be claimed as tested end to end.
- No tests of real devices, cyberattack penetration, IEC/ISO conformity, medical-grade alarms, or clinical deployment have been performed.
