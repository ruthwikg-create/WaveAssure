# WaveAssure v0.11.0 — Appearance and workflow verification

Date: 2026-10-24. Research engineering assessment; no clinical or hospital acceptance authority.

## Change set

- Workbench and dedicated reviewer page: System / Light / Dark theme selectors.
- Browser-local theme/motion preferences, with OS reduced-motion support.
- Theme-aware static ECG, PPG and ABP plot colors and signal-grid colors; actual source data and numerical analysis unchanged.
- Controlled decorative motion for navigation, panel entrances and hover states. No live physiological data animation or diagnostic implications.
- Clear focus outlines, improved informational text sizing, and dedicated reviewer form layout.

## Executed checks

| Check | Actual result | Scope |
|---|---|---|
| `python -m pytest -q` | 88 passed | Synthetic test fixtures, regression and theme/asset checks |
| `node --check web/theme.js web/app.js web/review.js` (each file) | Passed | Parsing/syntax only |
| Static Chromium: 1440px light and dark | Rendered | Browser `set_content`, local CSS/JS; no real HTTP browser navigation |
| Static Chromium: 390px mobile workbench | No horizontal document overflow observed | One viewport; not all mobile browsers |
| Static Chromium: 390px dedicated review | No horizontal document overflow observed | Dedicated UI, mocked reviewer API |
| Browser navigation: four workbench tabs | All accessible, no JS exceptions | Mocked/in-process bridge |
| In-process bridged API: create synthetic, render waveforms, fault, records, audit | Completed; three canvases and two stored synthetic/derived records; no JS exceptions | FastAPI TestClient bridge; not a network/browser-to-server acceptance test |
| Theme switch while record shown | Measurement value and record title unchanged | Representative synthetic record only |
| OS prefers-reduced-motion emulation | `data-motion=off` observed | Headless Chromium; OS emulation only |
| Contrast tokens | Defined foreground/background pairs >= 4.5:1 in light/dark | Token-level WCAG AA contrast, not full WCAG certification |

## Limitations / open defects

- Real Chromium `page.goto(http://127.0.0.1/...)` is blocked by this execution environment; browser tests use static loading and simulated in-process transport.
- Real Windows deployment, keyboard-only and screen-reader testing on physical devices remain open.
- Cross-browser Firefox/Safari acceptance, complete automated WCAG audit, and clinician usability evaluations remain open.
- Research classifier remains untrained without sufficient verified data; no sensitivity, specificity or clinical accuracy claims.
- All eight medical-device clinical-readiness gates remain unresolved. This is not an authorized healthcare application.
