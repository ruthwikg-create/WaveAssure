'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
require('../web/ecg-matrix.js');
const m=globalThis.WaveAssureECGMatrix;
const beat=(label,n=140)=>Array.from({length:n},(_,i)=>String((i%19-9)/15)).concat([String(label)]).join(',');
const a=beat(0),b=beat(1),csv=a+'\n'+b+'\n';
let kind=m.inspect(csv);assert.equal(kind.kind,'matrix');
assert.equal(kind.fields,141);assert.equal(kind.hasHeader,false);assert.equal(kind.suggestLabel,true);
assert.equal(m.rowLines(csv,false).length,2);
assert.equal(m.parseRow(a,true).length,140);
assert.throws(()=>m.parseRow(a+',3',false),/nonnumeric|minimum/i, 'fails unexpected label only when actually nonnumeric');
const columns=Array.from({length:140},(_,i)=>String(i)).concat(['label']).join(',');
kind=m.inspect(columns+'\n'+csv);
assert.equal(kind.kind,'matrix');assert.equal(kind.hasHeader,true);
assert.equal(m.rowLines(columns+'\n'+csv,true).length,2);
const named='time_s,ECG_mV\n0.00,1.1\n0.01,1.2';
assert.equal(m.inspect(named).kind,'not_matrix');
assert.equal(m.inspect('Patient Number,Heart Rate Alert\n1,0').kind,'not_matrix');
assert.throws(()=>m.parseRow(Array(140).fill('NaN').join(','),false),/nonnumeric/);
assert.throws(()=>m.parseRow(Array(140).fill('Infinity').join(','),false),/nonnumeric/);
assert.throws(()=>m.rowLines('',false),/Row count/);
assert.throws(()=>m.rowLines(Array(20002).fill(a).join('\n'),false),/8 MB text|Row count/);
const ui=fs.readFileSync(path.join(__dirname,'../web/index.html'),'utf8');
const app=fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8');
assert.equal((ui.match(/type="file"/g)||[]).length,1,'single upload input preserved');
for(const id of ['ecgMatrixPanel','ecgMatrixConfirm','ecgMatrixLabel',
                  'ecgMatrixHeader','ecgMatrixRow','ecgMatrixPreview','ecgMatrixCanvas']){
 assert.ok(ui.includes('id="'+id+'"'),id+' missing');
}
assert.ok(app.includes('WaveAssureECGMatrix.inspect(head)'));
assert.ok(app.includes('WaveAssureECGPreview.show(file,matrix)'));
assert.ok(app.includes('WaveAssureECGPreview.reset()'));
assert.ok(ui.includes('/static/ecg-matrix-ui.js'));
console.log('ECG segment matrix: headerless/indexed CSV, label exclusion, bounds, single picker and UI contract PASS');
