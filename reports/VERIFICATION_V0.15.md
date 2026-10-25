# v0.15 unified dataset picker — verification

Scope: one file-selection input for supported retrospective research recordings. No clinical-performance claims.

## Development tests

- Python `pytest`: 108 passing fixture-based software tests.
- Node checks for `app.js` and `dataset-upload.js`: passed.
- `node tests/dataset-upload15.cjs`: both supported formats and 11 invalid combinations checked.
- Chromium UI via real FastAPI TestClient through in-process API bridge: one file input, 300-row CSV import, incomplete `.hea` rejection, matched format-16 WFDB import, light theme change; zero page JavaScript errors. Data were synthetic.
- Direct Chromium navigation to localhost was blocked by the execution environment; a complete Windows-browser test on the user's own laptop has not been performed.

These software checks do not measure clinical classification accuracy, patient safety, or regulatory approval.
