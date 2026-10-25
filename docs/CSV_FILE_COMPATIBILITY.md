# CSV import compatibility and safety (research only)

WaveAssure's **Waveform review** accepts regularly sampled physiological **waveform samples**, not arbitrary patient tables. Accepted sources: de-identified mapped waveform CSVs or supported WFDB format-16 pairs. Uploading a patient-monitoring CSV does not mean it contains real-time ECG, alarm audio, or monitor logs.

## Why a monitoring-summary CSV fails

A table with columns such as `Patient Number`, `Heart Rate Alert`, `SpO2 Level Alert`, `Blood Pressure Alert`, or `Data Accuracy (%)` is **not** a waveform recording. Patient identifiers are prohibited even when their columns are not selected; status/alert/accuracy values must never be reinterpreted as ECG millivolts, photoplethysmogram samples, or arterial-pressure traces. A row number or patient number must never be used as elapsed time. Do **not** rename alert columns to bypass these checks.

If this is a fully synthetic patient table, the same structure restriction still applies. That kind of dataset needs a **separate tabular-data analysis workflow**, not waveform replay. Such a workflow is not provided by this import screen.

## Supported waveform CSV example (schema only)

```csv
time_s,ECG_mV,PPG_au,ABP_mmHg
0.00,0.08,0.40,90.0
0.01,0.09,0.41,90.1
```

The two rows above only illustrate column structure; they are **not** a valid recording. A valid CSV needs 100 to 100,000 timestamped samples, uniformly spaced (within 2%), with 50 to 1000 Hz sample rate, recording duration no longer than 600 s, elapsed time starting near zero, and correctly verified units. You must provide your own genuine recorded or expressly labelled synthetic **waveform** samples (not tabular outcome labels).

Use the **one** Upload research recording picker, select a CSV, confirm the time column and appropriate waveform channels, and click Import selected CSV. Unrecognized time-column names may be selected manually if they really contain elapsed seconds or milliseconds. No alarm is asserted unless the researcher supplies a timestamp, and any such timestamp is marked as unverified user annotation.

## Removing personal information

Work with appropriately de-identified **source** data before import; do not simply hide the identifier checkbox. The header checks are protective filters, **not** a complete privacy/de-identification system. Do not import real patient records or use the research prototype on a hospital network.

This fix makes incompatible datasets produce a clear explanation, **not** a new alert-classification, alarm-prediction or patient monitoring feature. This application is not clinically validated, certified or authorized for patient care.
