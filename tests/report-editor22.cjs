'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../web/report-editor.js'),'utf8');
const names=['studyLabel','studyId','age','sex','unit','recordedOn','reviewer','reviewerNotes'];
const fields=Object.fromEntries(names.map(id=>[id,{value:'',handlers:{},addEventListener(event,fn){this.handlers[event]=fn;}}]));
const output=Object.fromEntries(names.map(id=>[id,{textContent:'Not provided'}]));
const buttons={
 printEvidence:{addEventListener(event,fn){this.onClick=fn;}},
 clearDetails:{addEventListener(event,fn){this.onClick=fn;}}
};
let printed=0;
global.window={print(){printed++}};
global.document={
 getElementById(id){const v=fields[id]||buttons[id];assert.ok(v,id);return v;},
 querySelectorAll(selector){
   const match=/^\[data-patient="([a-zA-Z]+)"\]$/.exec(selector);
   assert.ok(match,selector);return [output[match[1]]];
 }
};
require('../web/report-editor.js');
assert.equal(output.studyLabel.textContent,'Not provided');
fields.studyLabel.value='<img src=x onerror=alert(1)>';
fields.studyLabel.handlers.input();
assert.equal(output.studyLabel.textContent,'<img src=x onerror=alert(1)>');
fields.age.value='210';fields.age.handlers.input();assert.equal(output.age.textContent,'Not provided');
fields.age.value='45';fields.age.handlers.input();assert.equal(output.age.textContent,'45');
fields.sex.value='Other / not specified';fields.sex.handlers.change();
assert.equal(output.sex.textContent,'Other / not specified');
fields.reviewerNotes.value='Review\nno diagnosis';fields.reviewerNotes.handlers.input();
assert.equal(output.reviewerNotes.textContent,'Review\nno diagnosis');
buttons.printEvidence.onClick();assert.equal(printed,1);
buttons.clearDetails.onClick();
for(const id of names)assert.equal(output[id].textContent,'Not provided');
assert.doesNotMatch(source,/\bfetch\s*\(|localStorage|sessionStorage|XMLHttpRequest|sendBeacon|document\.cookie/,
 'Study details must never leave the page or persist in browser storage');
assert.match(source,/target\.textContent\s*=/);
console.log('Report editor: local-only values, safe text, print, reset, age bounds PASS');
