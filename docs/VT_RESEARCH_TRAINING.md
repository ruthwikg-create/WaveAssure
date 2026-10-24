# WaveAssure VT Alarm Research Model v0.5.0

> Research / educational retrospective inference ONLY. NOT a medical device, not patient monitoring, not a clinical probability, and never a tool to suppress, rank, route, or silence alarms.

## What is new

- Consistent feature extraction from the **30 seconds before** VTaC VT alarm onset (300 s), never the 60-second post-alarm segment.
- ECG leads II, aVR, V, etc.; optional PLETH features; explicit treatment of missing data.
- Official dataset train / validation / test assignment loaded from `benchmark_data_split.csv`, with patient-record-level leakage rejection.
- A genuine scikit-learn regularized logistic regression baseline; no paid API and no pretrained weights represented as real.
- Sensitivity, specificity, counts (TP/FP/TN/FN), AUROC, AUPRC, Brier score on held-out **retrospective** partitions (only if data available).
- Machine-readable `metrics.json`, `skipped.json` (missing/corrupted waveform files), and checksum-protected **JSON** model coefficients. No unsafe pickle required in the app.
- Read-only explicit research inference button for **original imported WFDB records**, with the dataset's expert reference label kept strictly separate.
- All synthetic data and insufficient or single-class datasets remain **ineligible** for installed inference. `--smoke` outputs are rejected by the app.

## Requirements on Windows

Run from the new WaveAssure project folder in PowerShell, e.g. `D:\WaveAssure\WaveAssure`:

```powershell
cd 'D:\WaveAssure\WaveAssure'
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
```

Or run `scripts\train-vtac-windows.bat`, which installs free local ML dependencies and audits the dataset before attempting training.

**Metadata prerequisites**: both `D:\WaveAssure-Datasets\event_labels.csv` and `D:\WaveAssure-Datasets\benchmark_data_split.csv` must be present. If split CSV is missing, download the small official file (NOT the 18GB dataset):

```powershell
curl.exe -fL --retry 5 -C - -o 'D:\WaveAssure-Datasets\benchmark_data_split.csv' 'https://physionet.org/files/vtac/1.1/benchmark_data_split.csv'
```

**Data**: expert-labelled events' `.hea`/`.dat` pairs in `annotated_waveforms/<record>/<event>` (v1.1), or in `waveforms/<record>/<event>` (v1.0/v1.1), or individually in `sample/<record>/<event>`. Filenames and metadata must agree. VTaC v1.0/v1.1 labels and split identifiers are derived from the official dataset, never from synthetic waveforms. Incomplete and invalid WFDB files are skipped or rejected. Before feature extraction, the training program verifies the full shared-format-16 file byte count and per-channel WFDB additive checksums. Other WFDB layouts are intentionally skipped. This does not replace the official PhysioNet SHA256SUMS download-origin checks.

## Audit first (does not train)

```powershell
.\.venv\Scripts\python.exe benchmarks\train_vtac.py --root 'D:\WaveAssure-Datasets' --audit
```

The audit checks metadata and local **candidate file pairs**, not whether a pair is intact. Use `validate_waveassure_vtac.py` for a format-specific integrity check and the WFDB reader during model training.

## Generate a small, selective download plan (optional)

If your network cannot download the full 10.9 GB ZIP, you can generate a PowerShell script that requests only expert-labelled examples. It uses **only official labels and official split assignments**, and does not download automatically:

```powershell
.\.venv\Scripts\python.exe benchmarks\plan_vtac_download.py --root 'D:\WaveAssure-Datasets' --version 1.0 --output 'D:\WaveAssure-Datasets\download-selected-vtac.ps1'
```

The default plan selects 24 True and 24 False training events, and 7 of each for validation and test: 76 total (still only a software-development baseline, not adequate clinical validation). It produces file paths under `waveforms` for v1.0 and `annotated_waveforms` for v1.1. If your connection is too slow, stop/resume later; successful existing files are reused by curl where the server supports resuming. The script can be run after reviewing its contents:

```powershell
& 'D:\WaveAssure-Datasets\download-selected-vtac.ps1'
```

This will still require time and bandwidth. It does **not** avoid PhysioNet speed caps. The file pairs must be checked for integrity and adequate labels before use.

## Train and evaluate (requires genuine data)

```powershell
.\.venv\Scripts\python.exe benchmarks\train_vtac.py --root 'D:\WaveAssure-Datasets' --output models\vtac --dataset-version 1.0
```

The default training fails closed unless there are >=40 valid labelled events in `train`, and >=10 each in `validation` and `test`, **with both True/False labels in all three**. These are only implementation guardrails, NOT sample-size adequacy or clinical validation thresholds. More data are necessary for credible benchmark conclusions. Model will not be installed until this finishes successfully.

The only verified local file reported by the user is `sample/623dd0/623dd0_0023`, whose label is **True**. One example cannot train a binary classifier. This package does **not** contain that file, any personal data, PhysioNet waveform recordings, or any pretrained model.

On successful local training, `models\vtac\vt_model.json` is recognized by the browser interface after restarting/refeshing. Use the retrospective assessment button **only for research with imported original WFDB signals**. It is an exploratory score, NOT a validated clinical risk score.

### Engineering-only smoke testing

`--smoke --max-per-split 4` intentionally allows a tiny dataset for checking the code. Such results **must not** be called VTaC performance and are **rejected for app inference**. Tests under `tests/test_research_model.py` instead use generated numerical engineering fixtures that represent no patients.

## Limitations and risks

- Pre-alarm 30-second features were chosen as a basic transparent baseline. It is NOT a validated ventricular-beat detector; an ECG peak rate is not definitive VT evidence.
- Algorithm generalizability across hospitals, devices, noise conditions and patient groups has NOT been demonstrated.
- Future users could confuse a model's score with a clinical probability; output is explicitly marked uncalibrated retrospective research only.
- VTaC covers **ventricular tachycardia alarms**; it does not classify all monitor alarms, all arrhythmias, heart-rate high/low alarm categories, or patient deterioration.
- The classifier never talks to a real device, silences alarms, sends emergency alerts, or changes priority levels.
- This is not complete IEC 62304 / ISO 14971 / IEC 60601-1-8 conformance, clinical validation or regulatory approval.
- The published VTaC official splits are used to mitigate record-level leakage. Full independent external-site clinical validation, subpopulation analysis, prospective testing and performance confidence intervals are still needed.
- If dataset is sparse or connection fails, obtain more valid True and False examples rather than inventing labels or generating fake metrics.

## Source and license

VTaC v1.1: https://physionet.org/content/vtac/1.1/ (CC BY-SA 4.0, citation required). Research code: https://github.com/ML-Health/VTaC. This application only includes original code and publicly documented interfaces; dataset bytes are not redistributed.


## Preferred Windows workflow in v0.4

Run `scripts/prepare-train-windows.bat` once; rerun after interrupted downloads. It retrieves only an official labelled subset from VTaC v1.0, fits locally using the original official data partition and validation-only exploratory threshold, then installs a research-only JSON model **only** after genuine valid examples and all required classes are present. The training engine includes a constrained pure NumPy format-16 reader, removing the optional WFDB package dependency. This cannot bypass PhysioNet download limits.

`metrics.json` and `heldout_predictions.csv` appear only after a completed run. A small-subset benchmark is NEVER clinical accuracy validation. See `docs/CLINICAL_VALIDATION_ROADMAP.md`.

## Scientific release checks (v0.5.0)

- Use `--dataset-version 1.0` or `--dataset-version 1.1` to state which VTaC **waveform data** were actually downloaded. This must agree with the dataset manifest. Do not assume 1.1 simply because the label CSV originated there.
- For VTaC v1.1, download **the matching** official `SHA256SUMS.txt`, then use `scripts/verify_dataset_sha256.py` against the same-version files; do not use a mismatched version's SHA-256 checksums.
- A deliberately balanced 76-event training subset can be an **engineering smoke/development** study, not a scientifically defensible independent clinical validation; it changes event prevalence and precision estimates. Use an adequately powered full real-data evaluation for any submitted clinical model paper.
- No models/weights or trained-patient results are included in the public software ZIP.
