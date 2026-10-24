# WaveAssure — retrospective clinician-review usability protocol (draft)

**Research-only prototype v0.6.0. This is not a clinical trial protocol approved by an ethics committee. No trial is authorized by this document.**

## Study question
Can volunteer expert reviewers understand and use an offline research tool to examine de-identified historical ECG/PLETH recordings and document their opinions about previously recorded ventricular tachycardia alarms?

## Intended pilot scope
- Offline, non-interventional, retrospective assessment using publicly released VTaC data under its license; never collect data prospectively from live monitors in this release.
- Patient care, alarm suppression, nurse messaging, triage, diagnosis, clinical product claims and any real-time use are **excluded**.
- A researcher should obtain an ethics committee/IRB determination before involving human participants, even for a usability pilot. The pre-existing VTaC dataset's historical approval does not automatically cover a new study involving clinician participants or new data processing.
- Recruiting actual patients, integrating hospital records, clinical algorithm evaluation, or regulated investigational device research requires independent professional review and possibly additional approvals.

## Prerequisites
1. Authorize the dataset license and cite Lehman et al., *VTaC* 1.1, PhysioNet 2026, DOI 10.13026/jg2e-tf67.
2. Verify waveform completeness, source manifest SHA-256 where available, dataset split, and code version.
3. Maintain a separate study protocol, approval/waiver determinations, approved consent materials for reviewers where applicable, study governance plan, and access-controlled systems for any formal research.
4. Keep WaveAssure entirely on localhost and in an isolated research-only environment. It is **not designed to store personal health data**.
5. Remove any identifiers from reviewer notes; prefer generic anonymous reviewer codes.

## Reviewer workflow
- Import previously verified, licensed VTaC WFDB recordings and confirm channel identity.
- Select **Clinician review**, create anonymous reviewer code, and start a case snapshot.
- Review 15 seconds before the reference alarm without viewing the dataset reference within the pilot panel. Interpret True, False, or Indeterminate; grade confidence and signal quality.
- Submit one immutable response per case. Finalize after all cases.
- Export session-level JSON with per-case comparisons and integrity checksum. Preserve the original record hashes, code commit, dataset version and audit log with the report.

## Critical blinding limitation
The reviewer interface masks reference labels, but the **engineering workbench and its API still display expert labels**. There is no role-based authentication. Therefore this is an **interface-level hiding exercise, not a truly blinded clinician study**. To perform one, deploy a separate authenticated, restricted reviewer environment and use a protocol approved by the appropriate oversight body.

## Measurements and analysis
- Feasibility: percentage of successfully opened recordings, failed imports and completed sessions.
- Usability: task completion, clinician-reported difficulty, confusing elements and input validation problems. This release does not contain questionnaires; collect them separately under approved study procedures if needed.
- Descriptive agreement: True/False/Indeterminate decisions vs the public expert reference; report individual confusion counts and missing/indeterminate values. Small sample measures are not evidence of accuracy. Sensitivity/specificity display is suppressed when fewer than 30 cases per reference class.
- Inter-rater agreement, patient-cluster uncertainty, calibration, subgroup errors and model performance require separately specified analysis plans and substantially larger appropriate datasets.
- **This application does not generate model performance statistics until a separately trained genuine real-data model exists.** Clinician votes must never be presented as AI results.

## Operational limits and safety
- Keep software hosted only on `127.0.0.1` and used with **de-identified publicly released data**.
- No PHI, no live hospital network, no patient monitoring, no alarm alterations.
- Administrative access to the database or other engineering endpoints can read labels and change study material; no authenticated multi-user controls or audit signing exist.
- Validate a model separately before using it as an independent comparator. No performance claims may be made based on software unit tests.
- Explicitly label all session exports: *RETROSPECTIVE USABILITY PILOT; NOT CLINICAL VALIDATION*.

## Standards and regulatory roadmap (not compliance claims)
- Document lifecycle and risk-management activities referencing IEC 62304 and ISO 14971.
- Conduct human factors work referencing IEC 62366-1.
- Follow good machine learning practices and separate training, validation and independent testing; maintain data/model lineage.
- Consult local institutional ethics committee and applicable medical-device regulations (e.g., CDSCO in India) before starting any research with clinicians or patients that requires review.
- Prospective shadow studies and patient trials **cannot be run with v0.6.0**; they require trained models, cybersecurity controls, independent clinical validation, clinical governance, and formal approvals appropriate to intended use.

## Unmet publication/clinical readiness gates
- [ ] Enough distinct patient-level True and False VTaC alarms in official partitions
- [ ] Real trained model artifact, official provenance, reproducible training logs
- [ ] Independent held-out metrics including uncertainty and failure analysis
- [ ] Authenticated role-separated blinded review environment
- [ ] Ethics/regulatory determination and approved prospective protocol where applicable
- [ ] Multi-site/external evaluation, risk-benefit assessment, clinical safety review
- [ ] Documentation under organizational quality-management procedures

**Release decision:** Can be demonstrated as an offline, retrospective engineering/usability *prototype* only. **Not approved or ready for clinical trials.**
