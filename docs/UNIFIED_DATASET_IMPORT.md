# Single input for research recordings (v0.15)

Choose files using the **one** visible Upload research recording file selector.

- **CSV:** Choose exactly one `.csv`. Select the time column, time unit and waveform columns and units. The application does not infer actual physiological units or clinical meaning. CSV limit: 8 MB.
- **WFDB:** Hold **Ctrl** in the Windows file picker to select both the matching `record.hea` and `record.dat` at the same time. Only the app's constrained WFDB format-16 reader is supported; header limit 8,192 bytes, waveform data limit 1,600,000 bytes. This is not a generic DICOM, EDF or medical-device reader.
- The optional alarm timestamp is a user annotation, **not** a medical event classification. Files imported through the browser do not inherit official VTaC labels.
- The separate **Already have a WFDB research dataset on this computer?** expandable section is a server-local *path*, not another upload control. It supports the existing de-identified VTaC dataset workflow without uploading waveform bytes through the browser.
- Unselected/invalid file combinations show an actionable explanation. Files remain on the local WaveAssure research server; do not import patient identifiers or real clinical records without appropriate governance.

Clinical model training, clinical validation and hospital approval remain incomplete.
