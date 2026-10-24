# Contributing to WaveAssure

WaveAssure is a **research-only** open-source project. Contributions must not introduce patient-monitor control, clinical alarm routing, diagnosis or real clinical integration.

1. Open an issue describing expected behaviour and safety implications.
2. Make a branch with small commits, tests and a linked requirement/risk when applicable.
3. Use synthetic fixtures in tests; never upload patient identifiers, patient waveforms, PHI or API secrets.
4. Run `python -m pytest -q` and `python scripts/publication_audit.py`.
5. Document data provenance, scientific limitations, security impacts and exact reproduction commands.
6. State clearly when a model was not trained or externally evaluated. Do not label internal tests as clinical validation.

Before first public release, maintainer must replace the placeholder repository URL in `CITATION.cff`, review licensing of every new asset, check security dependencies, and approve the final scope and claims.
