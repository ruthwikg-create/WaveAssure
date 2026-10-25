# WaveAssure v0.20 — What can the alarm tooltip say?

WaveAssure can now show a **source-backed alarm category** and independently inspect **raw signal samples from every available ECG, PPG and ABP channel within ±2 seconds of the selected event time**. The event-context endpoint only reads existing local research samples; it does not change source records or create new alarm labels.

## For original VTaC recordings

- **Genuine VT alarm (source annotation)** means the VTaC dataset records this alarm as genuine ventricular tachycardia (VT). This is a **research dataset reference**, not independent real-time detection, clinical diagnosis, or a determination of ECG morphology subtype (such as monomorphic/polymorphic VT).
- **False VT alarm (source annotation)** means the source marked the VT alarm false. This **does not prove normal sinus rhythm**, and other problems may still exist.
- **Unverified user timestamp** has an unknown cause even if an ECG waveform appears near the orange marker.
- **DEMO marker** is a temporary display-only test marker. No patient monitor buzzed. Its optional beep is browser-generated, not evidence.

Hover over the orange EVENT marker in a particular ECG/PPG/ABP trace for its source reference and **observed raw amplitude range, mean and missing-sample count**. Click the orange line or **Explain alarm** to see the measured context from **all loaded channels**. The read-only numeric API is `GET /api/records/{id}/event-context?at_s=300` and rejects timestamps outside the recording.

## Why low/high alarm conditions and specific ECG types are not automatically shown

ECG `mV` samples are electrical voltage, not heart rate. A PPG waveform (a.u. or NU) does not supply a verified SpO₂ percentage. An arterial blood-pressure waveform (mmHg) alone cannot be compared with patient-specific monitor alarm settings to establish which configured limit triggered a buzzer. ECG morphology requires validated analysis and annotated reference data; the simple waveform preview does not classify AF, SVT, bradycardia, ventricular flutter, monomorphic or polymorphic VT, etc.

To determine if an actual bedside monitor alarm was **HR high / HR low, SpO₂ low, ABP high/low, asystole, arrhythmia, disconnection or device technical fault**, a research importer would need (a) original device event logs identifying alarm type and timestamp, (b) contemporaneous validated vital-sign numeric measurements, (c) the device's configured limits and alarm priorities, and (d) quality flags and source provenance. That validated event-log + numeric-vital workflow is **not yet present**. WaveAssure does not fabricate these values, ECG subtype classifications or normal/abnormal claims.

**Research only.** GitHub automated checks establish software functionality, not analytical/clinical validation, device certification or authorization for hospital patient care.
