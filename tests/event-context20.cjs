'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
require('../web/alarm-event.js');
const src=globalThis.WaveAssureAlarmEvent.explain;
const rec=(lab,timeSource,origin='wfdb_research')=>({metadata:{origin,parent_id:null},reference_label:lab,
 alarm_time_source:timeSource,alarm_time_s:300,source_reference:'Local VTaC research sample'});
let value=src(rec('True','dataset_annotation'),300);
assert.match(value.status,/genuine VT/i);
assert.match(value.reason,/ventricular tachycardia/);
assert.match(value.reason,/NOT an independent WaveAssure diagnosis/);
value=src(rec('False','dataset_annotation'),300);
assert.match(value.status,/false VT alarm/);
assert.match(value.reason,/does NOT establish a normal heart rhythm/);
value=src(rec('True','user_annotation_unverified'),300);
assert.match(value.status,/cause unknown/);
const app=fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8');
const api=fs.readFileSync(path.join(__dirname,'../waveassure/api.py'),'utf8');
const context=fs.readFileSync(path.join(__dirname,'../waveassure/event_context.py'),'utf8');
for(const label of ['function loadEventContext()', 'function renderChannelEvidence()',
 'channelObservationText(', 'eventContextRequestSequence', 'Event-window raw samples loading.',
 'ecg_morphology', 'Clinical low/high and normality not assessed']) {
 assert.ok((app+api+context).includes(label),label);
}
assert.ok(api.includes("'/api/records/{record_id}/event-context'"));
assert.ok(app.includes("window.WaveAssureAlarmEvent.explain(current,time)"));
console.log('VT source labels, unknown user annotations and raw channel context UI contract PASS');
