'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const src=fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8');
const start=src.indexOf('const CSV_IDENTIFIER_TOKENS=');
const end=src.indexOf('function showCSVMapping(', start);
assert.ok(start>=0 && end>start, 'CSV guard source must exist');
const context={};
vm.runInNewContext(src.slice(start,end)+'\nthis.csvFieldType=csvFieldType; this.csvColumnGuess=csvColumnGuess;',context);
const type=context.csvFieldType, guess=context.csvColumnGuess;
for(const h of ['Patient Number','Patient ID','Subject','MRN','Email']){
 assert.equal(type(h),'identifier',h);
 assert.equal(guess(h),'',h);
}
for(const h of ['Heart Rate Alert','SpO2 Level Alert','Blood Pressure Alert',
 'Data Accuracy (%)','ECG Alarm','Heart Rate','SpO2','Respiratory Rate']){
 assert.equal(type(h),'summary',h);
 assert.equal(guess(h),'',h);
}
for(const [h,expected] of [['time_s','time'],['Time (ms)','time'],['ECG_mV','ECG'],
 ['LeadII','ECG'],['PLETH','PPG'],['ABP_mmHg','ABP']]){
 assert.equal(guess(h),expected,h);
}
assert.ok(src.includes("time.value=timeName||'';"),'Do not use first CSV column as time');
assert.ok(src.includes("Boolean(identifiers.length)||!time.value||!checked"),'Invalid mapping must disable import');
console.log('CSV header mapping: identifier, alert, scalar, real waveform and time cases verified');
