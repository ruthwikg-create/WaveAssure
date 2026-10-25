# WaveAssure alarm-event explanations (v0.14)

This is **research software, not a medical device**. All recording reviews are retrospective.

## Files and timing

A supported WFDB `.hea` file defines the waveform layout, calibration, channel names and sample rate; its matching `.dat` file stores the sampled waveform. Both must use a format supported by WaveAssure (currently a constrained shared-file format 16 decoder). These files do **not** contain the original audible monitor buzzer.

A VTaC event verified by the *local* event-label file is placed at the dataset's documented 300-second alarm onset. A user-entered timestamp on a custom import is **unverified**. A recording without documented timing has **no alarm marker**. VTaC file authenticity still requires checking the official source and its integrity manifest; local WFDB checksums alone are insufficient.

## Event label interpretation

- **True VT reference:** the original research dataset labelled the recorded VT alarm genuine. This is not a WaveAssure model prediction or a real-time diagnosis.
- **False VT reference:** the original dataset labelled the VT alarm false. This **does not imply a normal rhythm**, and it does not rule out other abnormalities.
- **User-supplied timestamp:** the time is shown, but the reason an actual device alarmed remains unknown.
- **Unknown timing:** no source-backed event time exists, so no time or classification is fabricated.
- **Fault-derived record:** cannot inherit the original dataset event label.

Click **Explain alarm** (accessible by keyboard), **Jump to alarm**, or an orange waveform marker when visible to inspect these facts. Playback advances a recorded waveform window; it does not reproduce bedside monitor operation.

## Animation toggle

**UI effects on/off** changes decorative transitions and hover effects only. It does **not** change recorded waveforms, replay timing, numerical measurements, or any patient alarms. For historic waveform movement use **Play recording**. Reduced-motion operating-system preferences override decorative animations.

## Verification and limitations

Research-fixture tests in `tests/test_alarm_ui14.py` and `tests/alarm-event14.cjs` check truthful labels and controls. No real-world clinical accuracy, independent reviewer study, actual audible alarm reproduction, or hospital approval has been demonstrated.
