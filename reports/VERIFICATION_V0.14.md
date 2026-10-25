# WaveAssure v0.14 — Engineering verification (2026-10-25)

- Local `python -m pytest -q`: **105 passed**, synthetic fixtures; no clinical sensitivity/specificity measured.
- `node --check` for `web/alarm-event.js`, `web/app.js`, and `web/theme.js`: passed.
- `node tests/alarm-event14.cjs`: six non-clinical provenance scenarios passed.
- Real browser navigation in this execution environment: blocked by environment policy (`ERR_BLOCKED_BY_ADMINISTRATOR`). **No live browser or Windows site-acceptance claim.**
- Custom WFDB decoder, reference labels, imported timestamps and research-only application constraints remain as before.
- Clinical and regulatory gates: **BLOCKED**.
