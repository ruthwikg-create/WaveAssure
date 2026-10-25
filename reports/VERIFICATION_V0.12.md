# WaveAssure v0.12 — UI verification
2026-10-25. Research software; these are engineering checks, not medical validation.
- Original v0.11 local fixture baseline: 88 automated tests passed.
- v0.12 locally tested release: 91 automated tests passed, JS syntax passed.
- Headless Chromium local DOM: light and dark workbench/reviewer visual checks, mobile 390px zero horizontal overflow, no page errors.
- In-process API bridge: synthetic recording, 3 plots, derived fault, records and audit navigation completed without JS errors. Theme switch preserved displayed sampling frequency.
- Live localhost Chromium navigation on this execution platform was blocked, so Windows browser acceptance remains open.
- No clinical data, model training, risk control or regulatory authorization is added by this release. Clinical gate is BLOCKED.