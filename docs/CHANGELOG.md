## v0.18.0 — Recorded replay, event evidence and dataset guide (2026-10-25)

- Replace ineffective short-recording replay window motion with a visible moving recorded-time cursor and source-independent playback clock; avoid re-fetching unchanged windows.
- Display annotated event time and evidence-backed provenance in the Waveform review panel; add on-hover, focus and keyboard-accessible event explanations. The optional preview tone is browser-generated, not original monitor audio.
- Support display-only sample-index sweep for wide ECG matrices; no unverified units or rates assigned.
- Include in-app dataset-format guidance, a zero-PHI synthetic CSV generator and regression scenarios. Research only; clinical release remains blocked.

## v0.17.0 — Local ECG beat matrix preview (2026-10-25)

- Keep one research upload input; detect wide numeric CSVs as possible row-wise ECG segment datasets.
- Preview one ordered sample segment by row, using sample-index plotting and uncalibrated original amplitude values. Require an explicit researcher confirmation and expose header/last-label settings.
- Do not invent timing, sample rates, ECG millivolts, alarm occurrences, expert labels or clinical predictions; do not persist beat matrices as continuous waveforms.
- Add synthetic parser and browser-source contract regression tests. The uploaded third-party dataset has not been provided for independent inspection.

## v0.15.0 — Unified research recording file picker (2026-10-25)

- Replace three confusing file selectors with one upload control supporting one mapped CSV or one format-16 WFDB pair.
- Validate file counts, extensions, matching WFDB basenames and bounded sizes before the server performs its own validation.
- Explain errors in the UI; preserve advanced server-local WFDB path import without an extra upload input.
- Add automated single-input, file-combination and layout-hierarchy regression checks. No clinical capability claims.

## 0.14.0 — 2026-10-25 (alarm explanation and motion control clarity)

- Explain what a matched `.hea` header and `.dat` waveform file contain.
- Rename the misleading `Motion` switch to `UI effects`, separating decorative transitions from historical waveform replay.
- Add a keyboard-accessible **Explain alarm** button and optional clickable orange alarm timeline markers.
- Show the available research reference outcome: True VT/False VT dataset annotation, user-entered unknown-cause event, or unavailable event timing. Never imply a false VT label establishes a normal patient.
- Added six Node interpretation scenarios and UI contract tests; no classifier, diagnostic algorithm, or clinical approval was added.

## 0.13.0 — 2026-10-25 (recording replay and custom data)

- Replace static-only waveform review with recorded time navigation, pause/play, replay speed and event jump controls.
- Stop assigning 300 s to arbitrary waveform recordings; display only labelled VTaC timeline annotations or explicit user-supplied unverified markers.
- Enable custom CSV time/channel/unit mappings and bounded browser import of WFDB format-16 `.hea`/`.dat` pairs without granting expert labels.
- Add regression cases for time provenance, checksum rejection, unknown events, altered data, and unverified uploads. No clinical claims added.

## v0.11.0 — Accessible UI appearance (2026-10-24)

- Add System / Light / Dark theme preference with browser-local persistence.
- Add restrained premium CSS entry/hover animations and user/OS reduced-motion handling.
- Add theme-aware waveform colours without modifying research samples or measurements.
- Style dedicated reviewer interface and preserve unfinished assessments when switching themes.
- Add contrast-token, static-asset and presentation regression checks. Research-only; no regulatory gate closures.

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

## 0.12.0 — 2026-10-25 (engineering interface craft)

- Added maintainable CSS design layer for workbench and review UI; no external fonts/frameworks or remote assets.
- Replaced animated visual ornament with 140 ms optional interaction feedback and no signal animation.
- Clarified hierarchy and copy; fixed clipped mobile navigation with accessible labels and `aria-current` state.
- Added presentation regression checks and source-specific verification notes.
- Clinical study, model training and safety approvals remain open.


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
