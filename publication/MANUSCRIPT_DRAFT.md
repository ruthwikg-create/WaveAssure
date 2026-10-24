# WaveAssure: An Open-Source, Local-First Workbench for Reproducible Physiological Signal Assurance and Retrospective Ventricular Tachycardia Alarm Research

**Draft status: Methods and software description only. NOT a results paper.** Insert genuine experimental findings only after independently checking downloaded files, actual patient-record partitions, trained models and held-out performance. No clinical validity is claimed.

## Abstract (draft — no fabricated findings)

**Background.** False ventricular tachycardia (VT) alarms present an important research problem in ICU monitoring. Reliable software experimentation requires explicit separation of source labels, signal processing, model outputs and verification evidence.

**Objective.** To develop and openly distribute a local-first, research-only software workbench that supports constrained physiological waveform import, signal-quality experiments, source-preserving fault injection and reproducible baseline VT alarm research.

**Methods.** WaveAssure uses FastAPI, SQLite, browser Canvas, NumPy/SciPy and optional scikit-learn. It constrains WFDB imports to verified compatible shared-file format-16 signals, checks recording byte counts and per-channel WFDB checksums, and creates derived records without overwriting sources. A separate research pipeline extracts features from the 30-second pre-alarm interval, trains logistic regression on assigned VTaC development data, selects a threshold using validation records, and computes held-out test metrics. Software unit tests use synthetic fixtures exclusively.

**Results.** **[NOT YET AVAILABLE: report independently reproduced waveform coverage, cohort composition, held-out metrics, confidence intervals, subgroup errors and uncertainty from genuine records. Do not replace this with software test counts.]**

**Conclusion.** **[RESERVED until empirical results are available.]** The code is an educational/research tool, not a certified medical device or patient-alarm system.

## 1 Introduction

Physiological monitor alarms are important in intensive care, but false alarms can contribute to alarm fatigue. VTaC provides expert annotations of VT alarm events. Research on reducing false alarms must address the risk of missing genuine arrhythmias; software test success alone does not establish safety.

**Hypothesis:** A traceable, reproducible local pipeline can reduce engineering friction for retrospective method comparison. **Separate model hypotheses must be prespecified and tested on genuine, independent recordings.**

## 2 Materials and Methods

### 2.1 Study design

Retrospective computational methods study. No clinical decisions, alarm routing or real-time monitor connections.

### 2.2 Source data

VTaC version **[actual downloaded waveform version, to be filled]**. Cite official version and licence. The current latest v1.1 has 5,037 labelled alarm events; use official `event_labels.csv` and `benchmark_data_split.csv`. Report selected events/patients, exclusions and the data manifest. Do not pool multiple events from a patient across partitions.

### 2.3 Waveform processing

Signals are resampled to 250 Hz by VTaC. WaveAssure supports a restricted shared-file format-16 decoder. Gain, baseline, missing data and units are retained. The model reads 30 seconds directly before the VTaC reference alarm onset (300 s in each 360-second recording). Avoid use of post-alarm samples or expert labels in features.

### 2.4 Model specification

Transparent regularized logistic regression with training-only feature imputation/scaling, class-balancing and fixed hyperparameters. Threshold chosen on a held-out validation partition; the test partition must not be consulted during algorithm or threshold selection. Actual seed, package versions, class counts, exclusions and model coefficients must accompany a real training release.

### 2.5 Outcomes and analysis plan

Primary outcome: retrospective expert True-vs-False VT alarm classification. Prespecify sensitivity and false-negative rate in the full held-out cohort. Also report specificity, PPV, AUROC, AUPRC, Brier score, a confusion matrix, calibration and subgroup/error analyses as feasible. Class imbalance and multi-event patient clustering require appropriate uncertainty methods; available Wilson intervals assume event-level independence and are insufficient by themselves for a paper.

### 2.6 Software verification

Tests cover import boundaries, checksums, API safety, data integrity, provenance, train/validation/test partition guards, fitted-model parity and fault injection. Tests are engineering checks, not a demonstration of clinical diagnostic accuracy.

### 2.7 Ethical and regulatory considerations

The project uses publicly documented, de-identified research data under the data publisher's terms. Any new human-subject study, patient deployment or clinical evaluation would require separate institutional, ethical, privacy and regulatory review. No medical-device conformity or approval is represented by this release.

## 3 Results — intentionally unfilled

**Do not submit as a results paper until all items below are measured and documented:**

| Required result | Status |
|---|---|
| Total verified events and patient-record groups per split | NOT MEASURED |
| Expert labels and exclusions | NOT MEASURED |
| Trial model training and threshold | NOT PERFORMED ON COMPLETE DATA HERE |
| Held-out confusion matrix with per-class metrics | NOT AVAILABLE |
| Patient-cluster bootstrap CIs and calibration | NOT AVAILABLE |
| Protocol for external-site/vendor evaluation | NOT COMPLETED |
| Error-case review and label-disagreement analysis | NOT COMPLETED |

## 4 Discussion (outline only)

Discuss reproducibility and human-factors safeguards; contrast technical checks with model performance; explicitly address selection bias from missing waveforms, patient-event dependence, class imbalance, retrospective design and the danger of false reassurance from a supposed false-alarm prediction.

## 5 Data and code availability

**Code**: planned public GitHub release of WaveAssure, under the project MIT licence once reviewed. **Data**: downloadable separately from PhysioNet VTaC and subject to its own CC BY-SA 4.0 terms; no recordings bundled. Record actual release commit, DOI, model/dataset manifest and environment at time of submission.

## References

1. Lehman L et al. VTaC: A Benchmark Dataset of Ventricular Tachycardia Alarms from ICU Monitors. PhysioNet, version 1.1, 2026. doi:10.13026/jg2e-tf67.
2. Lehman L et al. VTaC: A Benchmark Dataset of Ventricular Tachycardia Alarms from ICU Monitors. NeurIPS 2023 Datasets and Benchmarks Track.
3. Collins GS et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models. BMJ. 2024;385:e078378. doi:10.1136/bmj-2023-078378.
4. International Medical Device Regulators Forum. Good Machine Learning Practice for Medical Device Development: Guiding Principles, final 2025.
