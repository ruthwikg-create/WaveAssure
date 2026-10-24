# Software Architecture Description (SAD) — v0.1.0

## Decomposition
- **UI** (`web/index.html`, `web/app.js`, `web/styles.css`): visualization only; no authoritative clinical computation; fetches from same-origin API.
- **API** (`waveassure/api.py`): request input validation, lifecycle orchestration and research-only response. No CORS wildcard and default bind localhost.
- **Contracts** (`waveassure/schemas.py`): fixed signal channel names/units, finite data, identical time grids, duration/sample limitations.
- **CSV boundary** (`waveassure/csv_input.py`): numeric time axis validation; unsupported/identifying columns rejected. Does *not* prove de-identification.
- **Analysis** (`waveassure/signals.py`): deterministic signal metrics and heuristics. Not validated against clinical reference instruments.
- **Storage/audit** (`waveassure/storage.py`): local SQLite, compressed record blobs, checksum verification, append-only-in-app linked audit hashes. Administrator can rewrite chain; no external signature.
- **Offline ML** (`benchmarks/train_vtac.py`): never invoked from API/UI. Training access and benchmark are separate research activities.

## Data flow
1. Synthetic generator or local CSV enters controlled ingress (API).
2. Pydantic enforces channel semantics and units, dimensions, length and finite values.
3. Record serialized, content SHA-256 computed, stored with UUID and provenance metadata.
4. Signal analysis yields check statuses and warnings. No clinical alarm prediction.
5. Fault request creates a distinct derived record, stores source UUID/parameters and audit event.
6. Report retrieves verified original blob, computes metrics and emits JSON with checksum.

## Quality attributes and restrictions
- Availability: best effort local standalone; no clinical uptime guarantees.
- Determinism: demos, feature extraction and faults deterministic with fixed seeds.
- Interoperability: CSV subset only v0.1.0; WFDB research benchmark separate.
- Security: not exposed to LAN/internet; no multi-user data separation; no privacy claims.
- Performance: input limited to <=100k samples/channel and <=3 channels.
- Maintainability: separated contracts, DSP, storage, HTTP layer; automated unit/integration tests.

## Failure handling
- Invalid sample units, nonfinite data, repeated timestamps, irregular sampling and nonexistent IDs rejected.
- Missing samples accepted as explicit null, counted in QC and interpolated solely for spectral analysis; source never altered.
- Audit hash break reported (does not detect malicious complete rewrite).
- No medical alarm is generated, modified or suppressed.
