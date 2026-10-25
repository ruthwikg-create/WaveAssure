# WaveAssure v0.13 engineering verification

**Date:** 2026-10-25
**Scope:** Local research UI and data imports, not a medical device or clinical trial.

## Reproduced previous shortcomings

- Review plot was static; no playback controls or progression of time.
- Orange event marker was hard-coded to 300 s for every waveform marked WFDB, creating false alarm implications on unrelated recordings.
- CSV importer demanded exactly the fixed `time_s` and a limited set of fixed signal column names; user datasets were rejected without mapping.
- Browser could not import its own WFDB `.hea` / `.dat` pair using a file picker.

## Implemented checks

- Python test suite: **100 passed** using synthetic fixtures.
- JavaScript syntax: `node --check web/app.js` passed.
- Browser DOM using Chromium with in-process FastAPI bridge: synthetic recording created, time advanced in playback, mapped CSV imported (including milliseconds, two channels and explicit user event time), WFDB pair imported (four calibrated channels, unverified user event time), alarm marker/jump shown, light theme, no horizontal overflow at 390px; no page JavaScript exceptions.
- Localhost navigation was blocked by browser sandbox (`ERR_BLOCKED_BY_ADMINISTRATOR`), so the DOM bridge is **not** an end-to-end browser/network acceptance test.
- No Windows machine available in this environment for the actual installed application.
- No clinical waveform sensitivity/specificity, medical alarms, real monitor interfaces or authorizations evaluated.

## Remaining limitations

- Large waveform preview requests decompress, validate and decimate a stored recording; smoothness depends on local CPU and file size. No frames-per-second SLA claimed.
- CSV import verifies numeric structure, units declared by the user and time consistency, **not** real signal calibration or patient de-identification.
- WFDB import is bounded to format 16 and does not authenticate published dataset SHA-256 values.
- All user-supplied event timestamps are unverified. The browser-generated optional preview sound is never the original monitor buzzer sound.
- **All clinical-readiness gates remain blocked.**
