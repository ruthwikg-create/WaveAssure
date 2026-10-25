# Wide ECG CSV segment preview (v0.17, research only)

The existing waveform importer accepts continuous time series with an elapsed-time column and physically meaningful ECG (mV), PPG (a.u./NU), or ABP (mmHg) samples. Some public ECG datasets instead contain **one heartbeat or ECG segment per row**, with 100–512 ordered numeric sample fields and, optionally, a final class label. These are different data structures.

## What this feature does

1. Extract a downloaded ZIP archive using **Extract All**, then choose the actual `.csv` file in WaveAssure's existing **Upload research recording** selector. ZIP archives themselves are not supported. Only one upload input remains.
2. For a suitable **wide numeric** CSV (100–512 fields per row; up to 8,000,000 bytes), WaveAssure opens a separate **ECG segment preview** rather than asking for a timestamp. It detects common numeric indexed headers (e.g. `0,1,2,…`) or numeric first rows; verify and override the **First row layout** setting yourself.
3. Confirm that each row contains **ordered, de-identified ECG samples**, not an alert/patient table. If the final column is a categorical benchmark label, select **Exclude final class/label column**; for common 141/188-column layouts this option is suggested but must be checked against the dataset's documentation.
4. Enter a **1-based row number** and click **Preview selected ECG segment**. The chart shows the original values against **sample index**, and sample count/min/max. Change the row to inspect another segment.

**This is a browser-local, bounded, single-segment visualization.** It does **not** convert or import a beat matrix into a continuous recording. It does **not** infer sample rate, duration, calibrated ECG millivolts, a heart rate, diagnosis, alarm event or training truth. The original dataset label is not interpreted as medical evidence. No values are uploaded to a server by this preview and no local research model is invoked.

The prototype still requires separate genuine timestamped WFDB/mapped CSV recordings to use full historical waveform replay, fault experiments and recorded alarm-marker workflows. In particular, DO NOT concatenate independently extracted beats into one apparent patient timeline or invent a 300-second alarm.

If a CSV has ordinary named columns, identifying fields, nonnumeric samples, or an unsupported shape, it may still be rejected. Do not rename identifying columns or labels to bypass privacy constraints. Work only with appropriately de-identified source data; this screen is not a privacy audit.

Verification covers synthetic fixtures and JS source/contract tests; successful automated tests do not establish that an arbitrary Kaggle CSV is authentic, that its units are valid, or that this software is medically validated.
