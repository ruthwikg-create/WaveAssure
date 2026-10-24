"""Printable, escaped offline research report. Not a clinical report."""
from __future__ import annotations
from html import escape


def report_html(report: dict) -> str:
    def safe(v): return escape('Not available' if v is None else str(v), quote=True)
    record=report['record'];reference=report['reference_annotation'];integrity=report['integrity']
    rows=''
    for window_name,window in report['descriptive_measurements'].items():
        for ch in window['channels']:
            fields=[window_name, ch['channel'],ch['unit'],ch['total_samples'],ch['valid_samples'],
                    ch['missing_samples'], ch['missing_fraction'],ch['minimum'],ch['maximum'],ch['mean'],ch['standard_deviation']]
            rows += '<tr>'+''.join('<td>'+safe(f)+'</td>' for f in fields)+'</tr>'
    limitations=''.join('<li>'+safe(s)+'</li>' for s in report['limitations'])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>WaveAssure research evidence {safe(record['id'][:8])}</title>
<link rel="stylesheet" href="/static/report.css"></head>
<body><div class="no-print"><p>Use your browser’s Print menu (Ctrl+P) to print or save as PDF.</p></div>
<h1>WaveAssure — Research Evidence Record</h1>
<p class="small">Schema {safe(report['schema'])} · Generated {safe(report['created_at_utc'])}</p>
<div class="box critical"><strong>RESEARCH USE ONLY — NOT A CLINICAL REPORT</strong><p>WaveAssure does not diagnose ventricular tachycardia, validate patient-monitor alarms, recommend treatment or establish clinical performance.</p></div>
<h2>Recording and provenance</h2><div class="box grid"><div><b>Record:</b> {safe(record['title'])}</div><div><b>Source class:</b> {safe(report['data_class'])}</div><div><b>Sample rate:</b> {safe(record['sample_rate_hz'])} Hz</div><div><b>Duration:</b> {safe(record['duration_s'])} s</div><div><b>Channels:</b> {safe(record['channel_count'])}</div><div><b>Source reference:</b> {safe(record['source_reference'])}</div></div>
<h2>Separate dataset annotation</h2><div class="box"><b>Reference label:</b> {safe(reference['label'])}<p>Origin: {safe(reference['type'])}. Independently adjudicated by WaveAssure: NO. Event timestamp: {safe(reference['event_time_s'])} seconds. This does not describe every moment of the recording.</p></div>
<h2>Descriptive sample measurements</h2><p class="small">Actual observed values, without interpolation, clinical limits, estimated rhythm diagnoses, or probability claims. Intervals use [start,end) seconds.</p>
<div class="scroll"><table><thead><tr><th>Window</th><th>Channel</th><th>Unit</th><th>Total</th><th>Valid</th><th>Missing</th><th>Missing fraction</th><th>Min</th><th>Max</th><th>Mean</th><th>Std dev</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Integrity and audit limitations</h2><div class="box"><p><b>Local data SHA-256:</b> <code>{safe(record['payload_sha256'])}</code></p><p><b>Current audit chain check:</b> {safe('Passed (not signed)' if integrity['audit_chain_currently_valid'] else 'Not verified / failed')}</p><p><b>Official dataset SHA-256 independently verified by this application:</b> NO</p></div>
<h2>AI and clinical decisions</h2><div class="box"><b>No medical decision provided.</b> Independent VT model result is not included in this evidence report. No alarm priority or intervention recommendation is calculated.</div>
<h2>Known limitations</h2><ul>{limitations}</ul><p class="small">Method {safe(report['measurement_method']['algorithm'])}. Population standard deviation; no propagated calibration uncertainty. Offline research software only.</p></body></html>'''
