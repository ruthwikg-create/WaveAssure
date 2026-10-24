# Intended Use and Safety Boundary — v0.1.0

**Intended use:** Local educational and research software for waveform visualization, signal preprocessing exploration, controlled fault-injection studies, software test evidence, and retrospective offline model experimentation.

**Users:** Biomedical engineering students, research engineers, verification engineers using **synthetic or properly de-identified research datasets**.

**Not intended for:** Clinical diagnosis, measurement for patient-care decisions, actual vital sign monitoring, alarm prioritization, alarm suppression, notification to nurses, treatment recommendations, life support, real-time connected clinical systems, or processing identifiable patient records.

**Claims that MUST NOT be made:** medical-grade, ISO certified, IEC 62304 conformant, IEC 60601 conformant, clinically validated, FDA cleared, CDSCO approved, approved medical device, or verified AI accuracy (without valid held-out datasets).

**Human factors:** Persistent prominent banner; data-origin labelling; unknown classifier displayed as NOT_AVAILABLE; no action button labelled "silence alarm"; inferred BPM labelled unvalidated estimate; QC pass wording limited to technical checks.

**Release blocker policy:** Do not introduce patient-facing or clinical integration capabilities without separate safety case, quality system, regulatory analysis, external validation, privacy/security infrastructure and prospective assessment by qualified specialists.

## Version 0.2.0 added scope
VTaC local-format research WFDB ingestion with retained ECG lead identifiers (II, aVR, V) and PLETH in normalized units; technical quality studies and source-preserving fault injections. The 300-second event reference is from the public dataset; the associated True/False label is not a software prediction. There is no arrhythmia detection or clinical alarm management.
