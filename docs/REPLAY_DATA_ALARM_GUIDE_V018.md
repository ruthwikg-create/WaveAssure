# WaveAssure research data, replay motion and alarm marker guide (v0.18)

**For research and education only; never for live patient monitoring, diagnosis, clinical notifications, bedside alarms or alarm suppression.** No genuine bedside monitor buzzer audio or real-time monitor event stream is bundled.

## What data to use in each feature

| Intended action | Required data | How to load it | Limitations |
|---|---|---|---|
| Test all workbench controls immediately | WaveAssure's built-in **Baseline**, **Fast rhythm**, or **Signal artifact** synthetic signals | Click one of the Data source demo cards | Engineering examples. No true patient event or original alarm. |
| Test your own CSV in full **Waveform review** | One de-identified, uniformly sampled time-series CSV with a time column in seconds/milliseconds and 1–8 ECG/PPG/ABP waveform columns with verified units | Single **Upload research recording** picker, map time + waveform columns, import | 100–100,000 samples, 50–1000 Hz, up to 600 s; 8 MB upload limit. No clinical diagnosis. |
| See an annotated VT alarm at the correct documented time | Compatible original VTaC WFDB **.hea/.dat** research recording (usually with local official dataset and `event_labels.csv`) | Existing server-local WFDB path import | Full annotated VTaC records may have documented 300 s reference onset. True/False refers to the source **VT alarm**, not a diagnosis or normality. No buzzer waveform is in ordinary ECG files. |
| Use your own WFDB recording | Matching format-16 `.hea` and `.dat` files | Select **both files together** in the one picker | Headers, checksums and constrained WFDB layout are validated. Other WFDB variants, EDF and DICOM not supported. User-entered timestamps are unverified. |
| Inspect Kaggle-style ECG beat/heartbeat CSV such as row-wise 140/187-sample arrays | Wide numeric CSV with independent ECG segments in each row | Choose CSV; confirm layout/class label; preview an individual row or **Sweep segment samples** | Sweep means ordered sample index, not measured seconds. No ECG voltage calibration, sample frequency, class meaning, alarm timing, or continuous patient timeline is inferred. |
| Inspect a patient alert table (`Patient Number`, `Heart Rate Alert`, etc.) | **Not a supported waveform format** | Use a dedicated tabular-analysis tool, not Waveform review | Alert flags are not raw ECG values or original buzzer timestamps. Identifiers are prohibited. |

For a guaranteed reproducible **synthetic test CSV**, from the repo root run:

```powershell
py -3 scripts/generate-research-waveform-csv.py
```

Choose `waveassure-demo-waveforms.csv` in the existing file picker. This deterministic file has columns `time_s,ECG_mV,PPG_au,ABP_mmHg`, **no patients, no expert labels and no real alarms**. The values are contrived sine functions; do not mistake them for normal ECG physiology.

### Recorded-time cursor vs UI effects

**Play recording** moves the bright green playhead through the original recording's elapsed-time axis. The waveform review window pans only when the playhead needs it. The green cursor also moves inside a short recording when the entire waveform is visible. Pause/seek do not modify the stored samples. The top toolbar **UI effects** button only toggles decorative CSS transitions and does not control replay. A wide ECG beat-matrix preview has a separate 3-second *display-only* sweep over sample indices.

### Alarm or buzzer evidence

An orange **EVENT** marker is shown **only** if an original research dataset annotation or user-entered timestamp exists. Mouse hover or keyboard focus on a waveform canvas reveals its time and evidence provenance; click or press Enter to open the longer explanation. For a labelled VTaC recording, the reference is *genuine VT alarm* or *false VT alarm* according to the source annotation. A **false VT reference is not proof of a normal patient**. Any arbitrary CSV/WFDB timestamp without a verified label is *cause unknown*. WaveAssure does **not** infer new true/false/normal decisions from the shape of the ECG.

Checking **Optional preview tone at timestamp** produces short **browser-generated audio** only when the recorded-time playhead crosses an annotated marker. A visible message records that the marker was reached. This is neither original monitor audio nor a clinical alarm. When no documented event time exists, there is no marker or simulated buzzer. In particular, an ECG sample matrix cannot supply historical monitor buzzer timing.

### Windows usage

```powershell
cd "D:\WaveAssure\WaveAssure-GitHub"
git switch main
git pull origin main
.\scripts\start-windows.bat
```

Open `http://127.0.0.1:8000`, press Ctrl+Shift+R to refresh JS, and confirm the expected version at top. No Windows device-level/browser-level acceptance test on the user's laptop has been run. Automated source and synthetic regression tests do not validate clinical accuracy, safety, or dataset authenticity.
