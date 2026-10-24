## v0.10.0 — Research integrity fixes (2026-10-24)

- Fail closed on corrupted gzip record payloads and mismatched stored metadata.
- Refuse local evidence mutations if audit-chain continuity fails.
- Snapshot review-session case hashes, rejecting changed recordings during review, finalization and export.
- Defend against stale overlapping frontend requests and duplicate reviewer-form submission; correct derived-record provenance display.
- Set Windows engineering launcher to engineering mode, independently of inherited review-mode environment state.
- Expand negative regression testing and CI JavaScript syntax checks.
- Browser DOM smoke used in-process HTTP test-client bridging because direct browser localhost navigation is restricted; this is not hospital or Windows acceptance testing.
- **None of the eight clinical release gates has passed. No genuine VT model training, external validation, or regulatory permission was obtained.**

## 0.9.0 (2026-10-24)

- Research model loader now requires externally pinned Ed25519 attestation; no self-hash-only activation.
- Dedicated local reviewer process with engineering-route denial and shared-key gate; not independent clinical blinding.
- Abstention on critically missing primary ECG features during runtime research assessment.
- Corrupt-record HTTP 409 handling, waveform-preview defaults, Windows CI test job configured.
- New adversarial regression tests and evidence report; no medical claims changed.

# Changelog

## 0.6.0 — 2026-10-24 (retrospective research reviewer pilot)

- Added localhost-only clinician reviewer usability workspace with anonymized review codes.
- Added recorded case snapshots, masked pre-alarm preview, immutable manual ratings and finalization.
- Added exportable dataset-label agreement reports and study-specific audit events; do not call them model results.
- Added explicit study protocol draft, safety/ethics restrictions and no-clinical-use gates.
- Continued to block VTaC model installation until genuine training on both labels completes.

## 0.5.0 — 2026-10-24 (research software release candidate)

- Enforced local-only HTTP peer and Host checks with cross-origin denial and browser security headers.
- Removed synthetic record ability to carry a purported expert reference label.
- Added SHA-256 verification against a version-matched PhysioNet manifest for local dataset files.
- Added direct-trainer patient-group leakage, duplicate-record and dataset version provenance checks.
- Added conservative publication audit, report and methods-only manuscript scaffold; never invent genuine training results.
- Added source code license, citation metadata, contributor guidance, code/data licensing notes and revised security disclosures.
- Updated visible version, requirements notes, release testing and provenance docs.
- Clinical use, compliance certification and independent clinical performance remain **not established**.

## 0.4.0
- Selective, resumable VTaC waveform acquisition and standalone research training pipeline.

## 0.3.0
- Model training, offline JSON model export, testing and model availability checks.

## 0.2.0
- WFDB constrained format-16 importer, channel preservation and 300-second marker.

## 0.1.0
- Local waveform workbench, synthetic demos, fault injection, SQLite and technical reports.
