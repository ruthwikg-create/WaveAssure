# WaveAssure
### Physiological Signal Assurance Workbench · Recorded Replay & Custom Import Research v0.13.0

> **RESEARCH / EDUCATION ONLY. NOT A MEDICAL DEVICE. NOT FOR PATIENT CARE, DIAGNOSIS, ALARM CONTROL, OR CLINICAL MONITORING.**

WaveAssure is an offline-first, full-stack biomedical research project. It loads time series, runs deterministic technical signal-quality checks, injects known faults, generates traceable engineering reports, and provides a separate **optional** training script for the public VTaC ventricular-tachycardia false-alarm benchmark.

See [interface design decisions](docs/INTERFACE_CRAFT.md), [appearance controls](docs/APPEARANCE.md), and [v0.12 verification evidence](reports/VERIFICATION_V0.12.md).

**v0.13.0 — Recorded-time waveform playback and user-mapped custom imports (research only):**
- Recorded waveform replay (pause, speed, window selection) and source-specific alarm timestamp markers; optional simulated tone is **not original monitor audio**.
- Guided CSV mapping for user-selected columns/units, and local browser upload for a restricted WFDB format-16 header/data pair. User annotations remain unverified and custom data never gain expert ground truth.
- See `docs/REPLAY_AND_CUSTOM_IMPORT.md` for supported inputs, safeguards and limitations.

**v0.12.0 — Intentional engineering interface (NOT clinical validation):**
- Replaced ambient gradients, moving navigation, luminous cards and showy animation with plain borders, measured spacing, restrained status colors and clear data typography.
- Compact mobile navigation now has accessible names rather than cut-off words; both operating themes and standalone reviewer page share one documented local CSS craft layer.
- Default decorative motion is off for new browser sessions; users may re-enable limited 140 ms interaction transitions. Operating-system reduced-motion preference still takes precedence.
- Preserved original recording-source distinctions, safety warnings, waveform data and all clinical/regulatory release blocks. Three additional presentation tests bring the local synthetic-fixture suite to 91 passing tests; in-process browser-workflow and offline layout checks were performed separately.

**v0.11.0 — Accessible appearance and decorative motion (NOT clinical validation):**
- Light, Dark and System colour themes across the engineering workbench and dedicated offline reviewer page, with browser-local preference storage.
- Reduced-motion support via OS accessibility setting and a manual decorative-animation switch. Waveform samples, measurements, and clinical claims are never animated or modified.
- High-contrast design token palettes checked for WCAG AA text contrast (selected defined foreground/background pairs); visible focus outlines, responsive layouts and theme-aware ECG/PPG/ABP canvas colours.
- Automated asset/contrast checks and headless Chromium DOM checks with static/mock API transport. Network-based browser acceptance and device/clinical validation remain out of scope.

**v0.10.0 — Evidence integrity and workflow reliability updates (NOT clinical validation):**
- Corrupt compressed record payloads and mismatched metadata now fail closed instead of returning an unhandled server error.
- New record and review writes are blocked when the local audit chain has been altered; this local chain is still neither externally timestamped nor independently protected.
- Review sessions snapshot each source record checksum and refuse subsequent reviews, finalization, or comparisons if the underlying source changed. These checks do **not** establish independent clinical blinding.
- The browser workbench rejects stale concurrent waveform responses, resets waveform window controls between recordings, distinguishes fault-derived data from original dataset recordings, and displays accurate audit integrity warnings.
- Six original new negative-regression tests plus one finalization test added, with **83 passing synthetic-fixture tests**; browser DOM flows were exercised in headless Chromium with an in-process API transport, **not** on a real network deployment or user Windows computer. Independent clinical/clinical-grade end-to-end testing remains missing.
- The GitHub CI workflow validates JavaScript syntax as well as Python tests.

**Previous v0.9.0 baseline:** Research engineering candidate with 76 locally passing fixture-based tests (not clinical or Windows acceptance tests); NOT an approved medical application or peer-reviewed results study. See [reports/PUBLICATION_READINESS.md](reports/PUBLICATION_READINESS.md), [publication/MANUSCRIPT_DRAFT.md](publication/MANUSCRIPT_DRAFT.md), [SECURITY.md](SECURITY.md), and [docs/DATA_RIGHTS.md](docs/DATA_RIGHTS.md). The package contains **no patient waveforms or model trained on real patients**. Source publication is possible after maintainer review and replacing the citation placeholder; an empirical research paper still needs genuine completed benchmark data and assessment.

**Current release does not contain a pretrained or clinically validated AI model.** It now includes training and JSON-model inference for retrospective research only; no model can be loaded until appropriate labelled data have been trained locally. Clinical alarm classification and suppression remain disabled. Neither passing quality checks nor estimated heart rate implies clinical fitness.

## v0.9.0 — Corrective engineering changes (NOT regulatory gate closure)

- **Model artifact trust fixed at the runtime boundary:** A self-computed JSON SHA-256 no longer activates a research classifier. A separate Ed25519 signature tied to a pin-able external public key is now mandatory. **The build includes no signer key and no patient-data-trained model.** The signature establishes file custody, not training truth, model accuracy, independent assessment or clinical certification.
- **Dedicated review-mode isolation:** Start a separate localhost-only process using a 32+-character shared review key. In that process, engineering API endpoints exposing reference labels return 403; uncredentialed reviewer calls return 401. This is **not independent study blinding**: administrators and researchers can still open the database directly, and shared reviewer keys are not hospital user identities. The engineering workbench remains explicitly unblinded.
- **Research inference may abstain** when essential primary-ECG features are unavailable or missingness is high. The numerical missingness threshold is an **unvalidated engineering heuristic**, not a clinically justified threshold.
- **Corrupt stored records** consistently produce an explicit HTTP 409 on supported endpoints rather than unexpectedly leaking a server error; waveform-preview query defaults corrected.
- **Safety assertions tested:** New synthetic adversarial tests exercise forged model signatures, changed signer IDs, access restrictions, missing review keys, unknown operating modes, and corrupted records. **No genuine VT event accuracy has been measured.**
- **Clinical release remains BLOCKED.** See `reports/CORRECTIVE_ACTION_V0.9.md`, `docs/REVIEW_MODE.md`, and `docs/MODEL_ARTIFACT_TRUST.md`. All eight high-level readiness gates still require further independent evidence or organizational approvals.

## v0.8.0 — Measured evidence, no invented clinical results

WaveAssure now produces a separate **evidence-first summary**: observed sample statistics, dataset annotation (not predicted), specific 30-second pre/post alarm windows, source and integrity evidence, and missing-validation warnings. A printable review-only HTML report is available from **View printable evidence**. The JSON report has an explicit schema and no diagnostic output. We corrected a prior bug that let a fault-derived signal retain the original reference annotation; derived records are now **Unlabeled**.

**Status:** Tests are automated software tests, not clinical trials. **No actual VTaC-trained model is bundled.** Independent device verification, standards conformity and clinical validation have not been completed. See [docs/OUTPUT_VALIDATION_SPEC.md](docs/OUTPUT_VALIDATION_SPEC.md) and [docs/RELEASE_NOTES_V0.7.md](docs/RELEASE_NOTES_V0.7.md).

## v0.6.0 — Clinician-facing retrospective reviewer pilot (NOT a clinical trial)

WaveAssure now has an **offline clinician-review workspace** for evaluating previously recorded, de-identified WFDB-format VTaC waveforms. It provides a label-hidden review queue, 15-second pre-alarm waveforms, immutable reviewer decisions, confidence/quality fields, an audit trail, and a final locked JSON report comparing reviewer decisions against the expert dataset reference. It does **not** provide a trained AI model and does **not** enable clinical use.

1. Import a verified-format **real labelled WFDB recording** in **Workbench** (`sample/623dd0/623dd0_0023` for the previously verified local file).
2. Open **Clinician review** in the sidebar, use a made-up anonymous code, and create a local review session.
3. Inspect pre-alarm channels, choose True / False / Indeterminate, enter quality and confidence. Decisions are locked on submission.
4. Finalize all cases; export the JSON comparison report. The dataset label is hidden **within the pilot workflow before finalization** but is available in the engineering workbench: **not independently blinded** and **not suitable for a regulatory clinical study as-is**.
5. With one verified True case, you may test usability only. Sensitivity/specificity fields remain empty for fewer than 30 examples of each reference class. Even with more data, these are not clinical validation metrics.

**The original sidebar pilot is unblinded engineering practice, not an independently blinded study. For a stricter local separation use the dedicated reviewer mode in [docs/REVIEW_MODE.md](docs/REVIEW_MODE.md).**

**No clinician access over a network:** this app has no user authentication, TLS, formal e-signatures, data de-identification, or clinical data-governance controls. It is unsuitable for live patient use, real-time alerts, registered clinical trials, hospital deployment, or clinical decision-making. Institutional ethics/regulatory determination must precede formal clinician research. See `docs/CLINICIAN_PILOT_PROTOCOL.md`.

**Why there is still no trained True-vs-False model:** the assistant does not have access to your Windows D: drive, cannot retrieve the full PhysioNet archive from this environment, and has received evidence of **only one fully verified True VT recording**. Using synthetic records as False cases would manufacture a deceptive model. The real VTaC training pipeline remains included for use when enough legitimate recordings are available.

## Train on your Windows laptop — dataset-aware, resumable (v0.6.0)

**No genuine VTaC classifier is bundled or trained in this ZIP.** Only one validated True VT waveform has been reported so far on your D: drive. The computer running this assistant cannot access your D: drive, so I cannot responsibly claim a trained model. The included Windows workflow can finish it using real expert-labelled data rather than fabricating samples or accuracy.

1. Keep `D:\WaveAssure-Datasets` and your real `sample/623dd0/623dd0_0023` intact.
2. Double-click **`scripts\prepare-train-windows.bat`** in this new project. It downloads the missing official `benchmark_data_split.csv`, selects only 76 labelled VTaC events (48 train / 14 validation / 14 test, balanced classes), and reuses already complete local files.
3. PhysioNet was slow on your connection; this may take hours. Safely stop with Ctrl+C, then run the **same script again** to continue incomplete downloads. It refuses to train if actual labelled waveforms are insufficient.
4. If enough records are available, the trainer writes **unsigned/unreviewed** `models\vtac\vt_model.json`, `metrics.json`, and `heldout_predictions.csv`. The app **continues to reject inference** until an authorized external research artifact reviewer checks provenance and signs the model, and the corresponding public key is pinned. This alone does not authorize clinical use.
5. **Retrospective test metrics are NOT clinical accuracy validation.** See `docs/CLINICAL_VALIDATION_ROADMAP.md`. Do not deploy into a hospital.

Internet is required only for data and dependency downloads; the model fits and runs locally without a paid AI API. No cloud training or time-based background job is running until you execute the batch file on Windows.

## Quick start (Windows, completely local)

1. Install Python 3.11+ (3.11 or 3.12 recommended).
2. Unzip the project. Double-click `scripts/start-windows.bat` or open PowerShell from the project folder:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn waveassure.api:app --host 127.0.0.1 --port 8000
```

3. Open http://127.0.0.1:8000
4. **Real VTaC recordings (new in 0.2.0):** if your existing folder is `D:\WaveAssure-Datasets`, double-clicking the Windows launcher automatically configures it. Paste `sample/623dd0/623dd0_0023` (no file extension) into **LOCAL WFDB RECORD** and click **Import verified WFDB**. If launching with PowerShell manually, first run `$env:WAVEASSURE_WFDB_ROOT = "D:\WaveAssure-Datasets"` in the same terminal. The import preserves all four channels: II, aVR, V and PLETH, and checks expected size and the WFDB 16-bit channel checksums. The PLETH `NU` unit is preserved as a relative uncalibrated signal, not SpO₂.
5. Use the waveform time slider to view 10, 30 or 60-second windows or the six-minute overview. The VTaC reference alarm onset is **300 seconds** into the recording. The label is shown as a dataset reference, never as a model prediction.
6. Select **Baseline**, **Fast rhythm**, or **Signal artifact**. These are deterministic **synthetic** examples, not patient recordings.
7. Choose a fault to create a derived record. Inspect the technical QC changes. Export a report.
8. Inspect **Records** and **Assurance log** to see provenance and integrity checks.

### Mac/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn waveassure.api:app --host 127.0.0.1 --port 8000
```

**Important:** Leave it bound to `127.0.0.1`. There is no authentication, TLS or database encryption. Do not put it on the internet, a hospital network, or connect it to a patient monitor.

## Prepare an open-source release / research manuscript

Run `python -m pytest -q --junitxml=reports/junit-v0.5.xml`, followed by `python scripts/publication_audit.py`. On Windows use `scripts\check-release-windows.bat`. The generated report separates *software test results* from *empirical model-performance evidence*. It will explicitly say **clinical accuracy not validated** even when tests pass.

- Include the [MIT licence](LICENSE) for original source, contributor policy and the [citation metadata](CITATION.cff); replace the placeholder repository URL before publishing to GitHub.
- Never commit `models/`, `.dat`, `.hea`, research patient files, raw data labels, `.env`, databases or secrets. See [.gitignore](.gitignore).
- Check each dependency licence and review privacy, intended use, local-only safeguards and source attribution.
- Use [publication/MANUSCRIPT_DRAFT.md](publication/MANUSCRIPT_DRAFT.md) **as a methods draft**, not a completed scientific publication. All results are deliberately unfilled.
- Use `python scripts/verify_dataset_sha256.py --root <dataset-folder> --manifest <version-matched-SHA256SUMS.txt>` for stronger original file integrity evidence when the official manifest is obtained; do not conflate this with a clinical validation.
- Public website deployment is **intentionally unsupported**; the unauthenticated FastAPI app is for localhost only.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v --junitxml=reports/junit.xml
```

## Real local WFDB format-16 import (v0.2.0)

**Only** single-file, interleaved 16-bit WFDB recordings with a shared `.dat` file and ECG/PLETH/ABP signals are supported. Up to 8 uniquely named channels, 100,000 samples each. Missing digital samples (`-32768`) are represented as missing values in the scientific analysis. More complex WFDB formats intentionally reject with a clear error. **This is NOT a general-purpose WFDB implementation.**

The backend imports only from `WAVEASSURE_WFDB_ROOT` to avoid an unrestricted file-reading API. It checks byte size and WFDB channel checksums before accepting real data. This is *not* official SHA256SUMS verification, clinical accuracy testing, or proof of original file authenticity. The original file remains unchanged. The imported recording is stored in a local, compressed SQLite blob. Keep the server bound to `127.0.0.1`; it has no secure login or PHI protections.

`event_labels.csv`, if present at the dataset root, can provide the source's `True` or `False` VT **reference label**. No actual alarm classification algorithm is installed or enabled. The event label describes a particular alarm around **300 s**, not the entire six-minute waveform. For licensing and citation, see the official [PhysioNet VTaC dataset](https://physionet.org/content/vtac/1.1/).

## Import research CSV

Only local **de-identified** research data. Allowed headers exactly:

```csv
time_s,ECG_mV,PPG_au,ABP_mmHg
0.000,0.003,0.55,80
0.004,0.005,0.56,81
...
```

At least 100 rows, regular timestamps (2% tolerance), frequency 50–1000 Hz, maximum 100,000 points per channel and 8 MB JSON text. A subset of channels is fine. Empty readings are treated as missing. All values must be finite and units correct. Identifier columns are rejected; however, this is **not a PHI de-identification tool**. Consent and de-identification are your responsibility.

## VTaC research-only model training (v0.6.0)

WaveAssure now has a **working offline research classifier training pipeline** and explicit post-training inference for original imported WFDB recordings. No real model is bundled because the only locally validated recording from the conversation is **one True VT event**, insufficient for true-versus-false training.

Read **[docs/VT_RESEARCH_TRAINING.md](docs/VT_RESEARCH_TRAINING.md)** before proceeding. On Windows, double-click `scripts/train-vtac-windows.bat`, or from PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
.\.venv\Scripts\python.exe benchmarks\train_vtac.py --root "D:\WaveAssure-Datasets" --audit
.\.venv\Scripts\python.exe benchmarks\train_vtac.py --root "D:\WaveAssure-Datasets" --output models\vtac --dataset-version 1.0
```

You **must** download official `benchmark_data_split.csv` (small metadata file), collect and verify sufficiently many **both True and False** labelled events across the official train/validation/test partitions. The training program refuses insufficient, single-class or leaking data rather than producing fictional medical AI results. A successful research-only model is serialized in checksum-protected JSON, not pickle. No model from the engineering smoke tests can be installed for inference.

## Architecture

```
Browser (Vanilla JS, HTML Canvas, CSS; zero CDN dependencies)
    │ localhost HTTP / JSON
    ▼
FastAPI (Pydantic validation / local-only backend)
    ├─ signal processing (NumPy / SciPy)
    ├─ deterministic fault injection (derived records)
    ├─ report builder (JSON, SHA-256 provenance)
    └─ SQLite (compressed waveform blobs, hash-linked audit trail)

Retrospective track: verified VTaC → feature extraction → official partitions → sklearn training → JSON model → explicit research-only assessment
```

### Capabilities shipped in v0.6.0

- Professional responsive, local browser user interface
- Complete local VTaC-format waveform import (ECG II/aVR/V and PLETH), 16-bit calibration and integrity checks
- Alarm-onset marker at 300 seconds, waveform window navigation, source reference labels separate from AI predictions
- Deterministic ECG/PPG/ABP **synthetic demo** and local CSV import
- Missing-sample, low-variance, clipping-suspicion, 50 Hz spectral component checks
- ECG R-peak-derived *research estimate* (not validated)
- Source-preserving dropout / noise / drift / clipping tests
- SQLite persistence with SHA-256 payload checksums
- Hash-linked local audit history (**not cryptographically signed**)
- JSON engineering report and visible disabled clinical classifier
- VTaC research-model training, offline artifact export, optional explicit retrospective inference (no trained model bundled)
- Automated backend tests plus engineering documentation

### Not implemented / future work

- Any clinically validated false-alarm AI or risk-benefit study
- Manufacturer-specific alarm decoding / IEC 60601 alarm conformance testing
- Real-device connection; no alarm suppression, nurse push, or audible clinical alerts
- FHIR integration, secure multiuser auth, TLS, PHI encryption, multi-site deployment
- Independent clinical evaluation, QMS, formal standards conformance or regulatory submission
- Real-data benchmark completion and external replication (blocked pending additional verified labelled waveforms)
- Arbitrary complex WFDB records (only the tested simple format-16 layout is supported)

See `docs/` for intended use, architecture, hazards, lifecycle practices, requirements, test strategy, security threat model and research-model governance.

## Cost / license

The source code in this package was created for this project. Open-source dependency licenses remain their respective owners' terms. No paid AI API, cloud hosting, dataset subscription or developer tooling is required to run the application locally. Internet is needed for first-time package installation.

## v0.8.0 — India clinical regulatory readiness audit

WaveAssure now bundles a conservative **source-based readiness audit**, actual gaps list, an Indian regulatory approval pathway, and a draft clinical evaluation plan. This is **documentation and a release gate, NOT a clinical upgrade or regulatory submission**. No ISO/CDSCO/EC authorizations are asserted or obtained.

Run `python scripts/clinical_readiness_audit.py --strict` (exit 2 means clinical release **BLOCKED**). Read `reports/CLINICAL_READINESS.md`, `regulatory/AUDIT_GAP_REPORT.md` and `regulatory/INDIA_APPROVAL_PATHWAY.md`. The clinical reviewer system is not a secure hospital multiuser system; do not deploy it on a hospital LAN or expose via public URL.
