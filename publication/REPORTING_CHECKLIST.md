# WaveAssure transparent-reporting and peer-review checklist

This is a **working checklist**, not a claim of adherence or external endorsement. TRIPOD+AI (BMJ 2024) contains a 27-item reporting checklist for clinical prediction-model studies. A scientific paper should complete the official checklist, not treat the mappings below as a substitute.

| Area | Evidence required for research publication | Current state |
|---|---|---|
| Intended use and clinical role | Exact retrospective task, intended population, no direct patient use | Defined; research only |
| Data provenance | VTaC version, DOI, licence, original file hashes, inclusion / exclusion flow | Dataset references; actual complete download pending |
| Sample size | A priori justification and class balance by cohort | Missing |
| Partitioning | Original train, validation, test groups; group leakage checks | Implemented in code; needs real-data audit |
| Preprocessing | Sampling, missing signals, units, features and leakage analysis | Documented baseline, unit tests |
| Algorithm | Linear coefficients, hyperparameters, fitted preprocessing | Implemented, no trained data delivered |
| Hyperparameter selection | Pre-registered candidates/criteria using training/validation only | Fixed baseline; exploratory threshold selection |
| Evaluation | Held-out confusion matrix, sensitivity/specificity CIs, AUPRC, AUROC, calibration | Calculators implemented; genuine metrics unavailable |
| Bias/fairness | Site, monitor vendor, quality strata and label disagreements if available | Not assessed |
| Uncertainty | Patient-group bootstrap, credible uncertainty, selection bias analysis | Not assessed; Wilson event-level intervals only |
| Robustness | Known noise, electrode dropout, missing PLETH, dataset shift | Synthetic faults implemented; evaluation pending |
| External evaluation | Independent hospital/vendor or independent external dataset | Not performed |
| Reproducibility | Dataset hash manifest, code release tag, environment, seeds and scripts | Partial; software evidence available |
| Clinical validation | Prospective protocol/clinical oversight, risk/ethics assessment | Not performed |
| Registration | Study plan or preregistration when appropriate | Not performed |
| Ethics and privacy | Dataset original IRB/terms; additional real clinical studies separately approved | VTaC terms identified; no new real-world study |
| Limitations and adverse potential | False-negative harm, label ambiguity, alarm-fatigue trade-off | Documented; mitigation not clinically proven |

Primary sources:
- VTaC v1.1: https://physionet.org/content/vtac/1.1/ (DOI 10.13026/jg2e-tf67)
- TRIPOD+AI: https://www.bmj.com/content/385/bmj-2023-078378 (DOI 10.1136/bmj-2023-078378)
- FDA/IMDRF GMLP: https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/good-machine-learning-practice-medical-device-development-guiding-principles

Do not publish fabricated results or confuse passing synthetic unit tests with real VTaC accuracy evidence.
