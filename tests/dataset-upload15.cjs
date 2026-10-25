'use strict';
const assert=require('node:assert/strict');
require('../web/dataset-upload.js');
const classify=globalThis.WaveAssureDatasetUpload.classify;
const f=(name,size=250)=>({name,size});
assert.equal(classify([f('leadII.csv')]).kind,'csv');
assert.equal(classify([f('LEADII.CSV')]).kind,'csv');
assert.equal(classify([f('pair.hea'),f('pair.dat',500)]).kind,'wfdb');
assert.equal(classify([f('pair.DAT'),f('PAIR.HEA')]).kind,'wfdb');
for(const files of [[],[f('pair.hea')],[f('pair.dat')],[f('one.csv'),f('two.csv')],
  [f('one.hea'),f('two.dat')],[f('one.hea'),f('one.dat'),f('one.csv')],
  [f('unknown.txt')],[f('zero.csv',0)],[f('giant.csv',8_000_001)],
  [f('pair.hea',8193),f('pair.dat')],[f('pair.hea'),f('pair.dat',1_600_001)]]){
 const answer=classify(files);
 assert.equal(answer.kind,'invalid',`Expected reject: ${files.map(x=>x.name).join(',')}`);
 assert.ok(answer.error);
}
console.log('Unified picker: CSV, matched WFDB and 11 invalid selections verified');
