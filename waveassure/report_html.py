"""Concise, escaped A4 research evidence with in-browser de-identified details.

Patient/study information is edited exclusively in the browser after the server
has rendered research evidence. It is never submitted to this API or stored.
This is NOT a clinical report, diagnosis, or approved medical device record.
"""
from __future__ import annotations

from html import escape


def report_html(report: dict) -> str:
    def safe(value):
        return escape('Not available' if value is None else str(value), quote=True)

    record = report['record']
    ref = report['reference_annotation']
    integrity = report['integrity']
    windows = report['descriptive_measurements']

    def fact(label, value):
        return (f'<div class="fact"><dt>{escape(label)}</dt>'
                f'<dd>{safe(value)}</dd></div>')

    labels = {
        'SYNTHETIC': 'Synthetic example',
        'IMPORTED_WFDB_RESEARCH': 'Imported WFDB research recording',
        'UNVERIFIED_CSV': 'Imported CSV (unverified)',
        'DERIVED_FAULT_EXPERIMENT': 'Derived engineering fault test',
    }
    origin = labels.get(report['data_class'], report['data_class'])
    if ref['type'] == 'EXTERNAL_DATASET_REFERENCE' and ref['label'] in ('True', 'False'):
        alarm_title = ('VT alarm: source marked genuine'
                       if ref['label'] == 'True' else 'VT alarm: source marked false')
        alarm_explanation = ('Ventricular tachycardia (VT) alarm reference from the research dataset. '
                             'This is not a WaveAssure diagnosis.'
                             if ref['label'] == 'True' else
                             'Source marked this VT alarm false; this does not establish normal physiology.')
    elif ref['event_time_source'] == 'user_annotation_unverified':
        alarm_title = 'User-marked time: cause unknown'
        alarm_explanation = 'Timestamp entered by the user; no verified alarm reason.'
    else:
        alarm_title = 'No documented alarm reference'
        alarm_explanation = 'No alarm event was established for this record.'
    timestamp = (f"{float(ref['event_time_s']):.3f} s from recording start"
                 if ref['event_time_s'] is not None else 'Not available')
    source = ('Original dataset reference (not independently verified)'
              if ref['type'] == 'EXTERNAL_DATASET_REFERENCE' else
              'User annotation (unverified)' if ref['event_time_source'] == 'user_annotation_unverified'
              else 'No verified event label')

    def channel_table(window):
        if not window or not window.get('channels'):
            return '<p class="empty-note">No channel measurements available.</p>'
        rows = []
        for ch in window['channels']:
            def number(v):
                return '—' if v is None else f"{float(v):.3f}"
            rows.append('<tr>' +
                        ''.join(f'<td>{safe(v)}</td>' for v in
                                (ch['channel'],ch['kind'],ch['unit'],
                                 ch['valid_samples'],ch['missing_samples'])) +
                        f"<td>{number(ch['minimum'])}</td>"
                        f"<td>{number(ch['maximum'])}</td>"
                        f"<td>{number(ch['mean'])}</td></tr>")
        return ('<div class="table-wrap"><table><thead><tr>'
                '<th>Channel</th><th>Type</th><th>Unit</th>'
                '<th>Valid</th><th>Missing</th><th>Min</th><th>Max</th><th>Mean</th>'
                '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')

    recording_facts = ''.join([
        fact('Recording',record['title']),
        fact('Source',origin),
        fact('Duration',f"{record['duration_s']} s"),
        fact('Sampling',f"{record['sample_rate_hz']} Hz"),
        fact('Channels',record['channel_count']),
        fact('Record ID',record['id']),
    ])
    event_facts = ''.join([
        fact('Event time',timestamp),
        fact('Alarm evidence',alarm_title),
        fact('Reference',source),
    ])
    patient_fields = (
        ('studyLabel','Patient / research label'),
        ('studyId','Study ID'),
        ('age','Age'),
        ('sex','Sex'),
        ('unit','Unit / department'),
        ('recordedOn','Recording date'),
        ('reviewer','Prepared / reviewed by'),
    )
    # Text-only placeholders are populated via textContent; never HTML from user input.
    patient_facts = ''.join(
        f'<div class="fact"><dt>{escape(label)}</dt><dd data-patient="{key}">Not provided</dd></div>'
        for key,label in patient_fields
    )
    pre = windows.get('pre_alarm_30s')
    post = windows.get('post_alarm_30s')
    around = ''
    for label,window in (('Before the event',pre),('After the event',post)):
        if window:
            around += (f'<h3>{label} <span class="window-time">'
                       f'{safe(window["start_s"])}–{safe(window["end_s"])} s</span></h3>'
                       + channel_table(window))
    if not around:
        around = '<p class="empty-note">No documented event window. Entire-recording measurements appear below.</p>'

    audit = ('Passed local integrity check (not digitally signed)'
             if integrity['audit_chain_currently_valid'] else
             'Local audit integrity not verified')
    title = safe(record['id'][:8])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>WaveAssure evidence {title}</title>
<link rel="stylesheet" href="/static/report.css">
<script src="/static/report-editor.js" defer></script>
</head><body>
<section class="editor no-print" aria-labelledby="details-heading">
  <div class="editor-heading"><div>
    <h1 id="details-heading">Prepare evidence report</h1>
    <p>Add de-identified research details. The printable preview updates below.</p>
  </div><div class="editor-actions">
    <button type="button" id="printEvidence">Print / Save as PDF</button>
    <button type="button" id="clearDetails" class="secondary">Clear details</button>
  </div></div>
  <p class="privacy-note">Research prototype: use synthetic or de-identified details only. Do not enter real names, MRN/UHID, contact details or hospital patient records. Entries remain in this browser page until it is closed; they are not sent to the server or saved.</p>
  <div class="editor-grid">
    <label>Patient / research label <input id="studyLabel" maxlength="80" autocomplete="off" placeholder="e.g. Research subject A"></label>
    <label>Study ID <input id="studyId" maxlength="50" autocomplete="off" placeholder="e.g. SYN-001"></label>
    <label>Age <input id="age" type="number" min="0" max="120" step="1" autocomplete="off" placeholder="Optional"></label>
    <label>Sex <select id="sex"><option value="">Not specified</option><option>Female</option><option>Male</option><option>Other / not specified</option></select></label>
    <label>Unit / department <input id="unit" maxlength="60" autocomplete="off" placeholder="e.g. Research lab"></label>
    <label>Recording date <input id="recordedOn" type="date" autocomplete="off"></label>
    <label>Prepared / reviewed by <input id="reviewer" maxlength="80" autocomplete="off" placeholder="Role or reviewer code"></label>
    <label class="wide">Reviewer notes <textarea id="reviewerNotes" maxlength="1000" rows="3" placeholder="Optional engineering or research review notes"></textarea></label>
  </div>
</section>
<main class="paper" id="printableEvidence">
  <header class="report-head">
    <div><div class="report-brand">WAVEASSURE</div>
      <h1>Research Evidence Report</h1>
      <p class="subtle">Retrospective waveform record and source annotations</p></div>
    <div class="research-tag">RESEARCH USE ONLY</div>
  </header>
  <section class="report-section">
    <h2>1. Patient / research details</h2>
    <dl class="fact-grid">{patient_facts}</dl>
    <div class="notes"><strong>Reviewer notes</strong>
      <p data-patient="reviewerNotes">Not provided</p></div>
  </section>
  <section class="report-section">
    <h2>2. Recording details</h2>
    <dl class="fact-grid">{recording_facts}</dl>
  </section>
  <section class="report-section">
    <h2>3. Event summary</h2>
    <dl class="fact-grid">{event_facts}</dl>
    <p class="explanation">{safe(alarm_explanation)}</p>
  </section>
  <section class="report-section">
    <h2>4. Signal evidence</h2>
    <p class="section-note">Observed original waveform sample values. Min, max and mean are amplitudes in the supplied units, not normal/abnormal clinical assessments.</p>
    {around}
    <h3>Entire recording</h3>
    {channel_table(windows.get('entire_recording'))}
  </section>
  <section class="report-section trace">
    <h2>5. Record traceability</h2>
    <dl class="fact-grid">
      {fact('Local audit',audit)}
      {fact('Original dataset authenticity','Not independently verified')}
      {fact('Report generated (UTC)',report['created_at_utc'])}
    </dl>
    <p class="hash">Data SHA-256: <code>{safe(record['payload_sha256'])}</code></p>
    <p class="subtle">Source: {safe(record['source_reference'])}</p>
  </section>
  <footer class="report-footer">
    <strong>No medical decision provided.</strong> Research evidence only; not a clinical diagnosis, validated alarm assessment, or patient-care report.
  </footer>
</main></body></html>'''
