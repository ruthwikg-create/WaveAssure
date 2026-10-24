# WaveAssure VT Research Model Card — v0.5.0

**Status: NOT TRAINED ON GENUINE VTaC DATA IN THIS PACKAGE. No clinical validation.**

Task: retrospective True vs False ventricular tachycardia alarms only. Dataset: https://physionet.org/content/vtac/1.1/ .

Transparent CPU baseline: 16 features from 30 seconds before the 300 s alarm onset, training-only imputation and standardization, regularized logistic regression. 95% sensitivity target on validation is an exploratory optimization target, not a clinical safety threshold. Held-out test statistics must be reported honestly with counts and intervals, once genuine waveforms are accessible.

Risks: small-sample uncertainty, multiple events from patients, label ambiguity, vendor/hospital variation, noise and motion artifacts, missing channels, missed True VT and uncalibrated probabilities. No alarm suppression, clinician replacement, medical certification, or clinical safety claim. See CLINICAL_VALIDATION_ROADMAP.md.
