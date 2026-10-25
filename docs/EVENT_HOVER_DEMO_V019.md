# Why no alarm line is visible (WaveAssure v0.19 research interface)

An ECG, PPG or ABP waveform **does not automatically contain the monitor's alarm log**. The line appears only when the source has an alarm timestamp or the operator deliberately creates a **temporary DEMO event**. The browser's optional tone is synthesized by WaveAssure, not audio recovered from a medical device.

## To try the event line and hover explanation

1. Open the Waveform review with the **Baseline** synthetic recording or load a compatible timestamped CSV such as `waveassure-demo-waveforms.csv`.
2. If the selected record contains no alarm annotation, click **Show test event marker**. This places a temporary browser-only orange **DEMO** line at 5 seconds in a 20-second recording, or halfway for recordings shorter than 10 seconds. No modification to the stored original data or source event history occurs.
3. Hover within the orange line, or tab-focus the graph. Its tooltip says **DEMO event — no actual alarm detected**, the marked time, and why the optional preview beep plays. Click the orange line or press Enter on the focused graph to open the detailed explanation.
4. For a sound demonstration, check **Optional preview tone at timestamp** and click **Play recording**. At the orange marker you may hear a generated beep. The label explains that the beep is artificial and cannot be used to infer a patient's condition. Choose **Remove test marker** to clear it.
5. For an **actual documented research event**, use a compatible VTaC WFDB event with available reference annotation, or a de-identified waveform CSV whose alarm time was independently obtained from a real event log and manually entered at import. The latter remains **user-entered and unverified** in WaveAssure, and the system does not know the reason without separate evidence.

## What the hover can and cannot establish

- **Reference: genuine VT alarm:** A VTaC research source labels the original VT event as true, but independent clinical validation of WaveAssure has not occurred.
- **Reference: false VT alarm:** A source labels that specific VT alarm false; the patient's normality or other abnormalities cannot be inferred.
- **User-marked alarm — cause unknown:** A person entered the timestamp, not a cause.
- **DEMO event — no actual alarm detected:** The line and optional beep were generated solely to demonstrate the interface.
- **No event:** With no metadata or manual demo marker, a recorded buzzer time cannot be located.

### Important limitations

No hospital patient data, live vital-sign monitor connection, original bedside audio, alarm threshold metadata, or real-time nurse alert integration is included in this research workflow. The visual simulation does not classify abnormal health conditions or record a medical alarm. GitHub CI passing is not clinical validation.
