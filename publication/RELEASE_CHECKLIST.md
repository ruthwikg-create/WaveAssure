# Open-source release checklist

This package is a **source-release candidate**, not a published GitHub release and not a clinical paper.

- [x] Source files, basic local run instructions, tracked code version
- [x] MIT license for original source; separate dataset licence documented
- [x] Citation metadata provided; **repository URL still requires replacement**
- [x] Software test suite executed against synthetic test fixtures
- [x] API loopback guard, request Origin/Host checks and safety headers added
- [x] Documentation of intended use, risks, software assurance, security limitations and provenance
- [x] Official PhysioNet dataset SHA256SUMS verification script added
- [x] Manuscript methods draft and reporting checklist provided without fabricated metrics
- [ ] First public GitHub release reviewed and created by maintainer
- [ ] Replace `CITATION.cff` placeholder URL, confirm author's preferred attribution and repository ownership
- [ ] Independent reproducibility run on Windows Python 3.11 and separate environment; capture release commit and dependencies
- [ ] Full real VTaC labelled dataset integrity and model benchmarking confirmed
- [ ] Independent clinical/real-world validation and regulatory approval, if clinical deployment is ever planned

To publish **source only** after review: create an empty public GitHub repository, extract this package, run `git init`, `git add .`, `git commit -m "WaveAssure v0.6.0 local research release"`, set the remote, push, then create a tagged release `v0.6.0` with the ZIP and limitations. Never upload patient datasets, database records, environment variables, or trained weights by default. A Zenodo repository integration may later mint a citable release DOI; a DOI is **not** peer review or clinical validation.
