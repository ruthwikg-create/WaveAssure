/* Provenance-driven alarm explanation; NEVER diagnose from sampled waveforms. */
(function (root) {
  'use strict';
  function explain(record, timeSeconds) {
    const unknown = {
      status: 'Event type undetermined',
      classification: 'No verified VT reference decision is available.',
      reason: 'WaveAssure has not classified this recording. A visible waveform or timestamp alone cannot establish whether the person was normal, whether VT occurred, or why a monitor buzzed.',
      source: 'No expert-labelled event evidence supplied.',
      disclaimer: 'No live monitor audio, clinical diagnosis, or clinical alarm assessment is available.'
    };
    if (!record || !record.metadata || !Number.isFinite(timeSeconds) || timeSeconds < 0) {
      return Object.assign({}, unknown, {status: 'No recorded alarm timestamp', source: 'No timestamp is documented for this recording.'});
    }
    const meta = record.metadata;
    if (meta.parent_id) return Object.assign({}, unknown, {status:'Derived record — event not verified', source:'This is an artificially modified waveform. Source labels must not carry over.'});
    const label = record.reference_label;
    const annotated = meta.origin === 'wfdb_research' &&
      (record.alarm_time_source === 'dataset_annotation' ||
       (record.alarm_time_s == null && String(record.source_reference || '').includes('VTaC')));
    if (annotated && (label === 'True' || label === 'False')) {
      return {
        status: label === 'True' ? 'Reference: genuine VT alarm' : 'Reference: false VT alarm',
        classification: label === 'True' ? 'Expert dataset annotation: True VT.' : 'Expert dataset annotation: False VT.',
        reason: label === 'True'
          ? 'The VTaC dataset marks this recorded VT alarm as genuine. This is an annotation from the research dataset, NOT a WaveAssure prediction or a new patient diagnosis.'
          : 'The VTaC dataset marks this VT alarm as false. This does NOT establish a normal heart rhythm or rule out other abnormalities.',
        source: record.alarm_time_source === 'dataset_annotation'
          ? 'Local VTaC event_labels.csv and documented VTaC alarm onset; independent file authenticity not established.'
          : 'Legacy VTaC reference data; original alarm time was not separately stored. Confirm against the official source.',
        disclaimer: 'Do not use this reference annotation for patient care, alarm silencing, or treatment. No recorded buzzer audio is included.'
      };
    }
    if (record.alarm_time_source === 'user_annotation_unverified') {
      return Object.assign({}, unknown, {
        status: 'User-marked alarm — cause unknown',
        source: 'Timestamp supplied by the user; no expert rhythm/event label or original buzzer audio was provided.'
      });
    }
    return unknown;
  }
  root.WaveAssureAlarmEvent = Object.freeze({explain});
})(typeof window === 'undefined' ? globalThis : window);
