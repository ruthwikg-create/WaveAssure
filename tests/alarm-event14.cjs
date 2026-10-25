'use strict';
const assert = require('node:assert/strict');
require('../web/alarm-event.js');
const interpret=globalThis.WaveAssureAlarmEvent.explain;
const rec=(label,source,origin='wfdb_research',parent_id=null,time=300)=>({
  metadata:{origin,parent_id}, reference_label:label,alarm_time_source:source,
  alarm_time_s:time,source_reference:'Local VTaC research record sample/623dd0/623dd0_0023'
});
const a=interpret(rec('True','dataset_annotation'),300);
assert.match(a.status,/genuine VT alarm/);
assert.match(a.reason,/NOT a WaveAssure prediction/);
const b=interpret(rec('False','dataset_annotation'),300);
assert.match(b.status,/false VT alarm/);
assert.match(b.reason,/does NOT establish a normal heart rhythm/);
const c=interpret(rec('Unlabeled','user_annotation_unverified'),50);
assert.match(c.status,/cause unknown/);
assert.doesNotMatch(c.reason,/confirmed|diagnosed|normal patient/i);
const d=interpret(rec('True','user_annotation_unverified'),50);
assert.match(d.status,/cause unknown/); // Forged label cannot override provenance.
const e=interpret(rec('True','dataset_annotation','wfdb_research','derived-parent'),300);
assert.match(e.status,/not verified/);
const f=interpret(rec('True','dataset_annotation'),null);
assert.match(f.status,/No recorded alarm timestamp/);
assert.match(f.disclaimer,/No live monitor audio/);
console.log('6 provenance-driven alarm explanation scenarios passed');
