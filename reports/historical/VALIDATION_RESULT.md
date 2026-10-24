# WaveAssure 0.2.0 — Verification results

Executed on 2026-10-24 in the development container, not on the end-user Windows machine.

- `python -m pytest -q`: **25 passed**.
- `node --check web/app.js`: passed JavaScript syntax validation.
- FastAPI TestClient: imported synthetic WFDB format-16 with ECG II, aVR, V and PLETH; source-label lookup, calibration, individual channel fault injection, waveform preview and report checked.
- Negative tests: truncated .dat, modified digital samples, path traversal and unsupported formats rejected.
- Additional **90,000 samples per channel** (250 Hz, 360 seconds, 4 signals) synthetic WFDB stress fixture passed backend import, analysis, time window preview and JSON report.
- Chromium browser test in this environment: **blocked by administrator localhost restrictions**, so it is **not counted as passed**. Screen behaviour must be verified on the target Windows machine.
- Real VTaC `623dd0_0023` was **not available in the development container** and has NOT been decoded here. The user separately validated 720,000 bytes and four digital sample checksums using a local tool.
- No trained/validated VT classifier, no clinical alarm output, no clinical accuracy claim, no regulatory certification.

The implementation supports local, four-channel, common-file, little-endian 16-bit WFDB recordings with bounded sizes and explicit channel types. It does not support every legal WFDB header or compound layout.
