# Security policy — research prototype

**Do not expose WaveAssure on the internet, a hospital network or to sensitive personal health data.** This version is only suitable for an isolated local research machine with appropriately de-identified datasets.

Security issues: report privately to the repository maintainer after the public repository is created. Do not upload test data containing patient identifiers.

## Current controls

- Default Windows/Python commands bind to `127.0.0.1`.
- ASGI middleware checks the peer is local and the HTTP Host is an allowlisted loopback name, refusing DNS-rebinding and direct remote access.
- Cross-origin requests are refused; explicit security, cache, CSP and framing headers are present.
- Strict bounded request body length (content-length), schema-validated API input, constrained file imports.
- Data source preserved via record checksums and hash-linked local audit history.
- Optional VTaC SHA-256 manifest verification. Research model loading now requires both a checksum and a separately pinned Ed25519 signature of attestation metadata. This confirms integrity relative to a configured key, **not the accuracy or truth of provenance claims**.

## Known gaps

There is **no hospital-grade** account authentication, role-based authorization, TLS, encryption at rest, externally anchored audit log, CSRF token, rate limiting, independent security audit, or secure multi-user deployment. The dedicated review mode uses only a shared secret and process-level API separation; it is not independently blinded. Host/Origin checks do not create a secure deployment boundary behind a reverse proxy. Local users and processes can rewrite the audit DB or substitute their own trust keys. This application must remain local-only; do not bypass its guards.

A real clinical/hosted application requires a separate security architecture, authorization and privacy threat assessment, vulnerability management, software bill of materials, controlled third-party data handling, and formal verification.
