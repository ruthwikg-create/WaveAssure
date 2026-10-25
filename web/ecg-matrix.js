/* Research-only preview of wide, numeric, row-wise ECG sample matrices.
   Deliberately separate from the physiological recording importer.
   Neither elapsed time, sample rate, amplitude units nor clinical labels are inferred. */
(function(root){
 'use strict';
 const MIN_SAMPLES=100,MAX_FIELDS=512,MAX_ROWS=20000;
 function cells(line){
   if(typeof line!=='string'||line.length>100000||/[\r\n]/.test(line))throw Error('Invalid CSV row');
   const out=[];let token='',quoted=false;
   for(let i=0;i<line.length;i++){
     const ch=line[i];
     if(ch==='"'){
       if(quoted&&line[i+1]==='"'){token+='"';i++}
       else quoted=!quoted;
     }else if(ch===','&&!quoted){out.push(token.trim());token=''}
     else token+=ch;
   }
   if(quoted)throw Error('Unclosed quote in CSV row');
   out.push(token.trim());
   if(out.length>MAX_FIELDS)throw Error('Too many CSV columns (maximum '+MAX_FIELDS+' for ECG segment preview)');
   return out;
 }
 function numeric(s){return typeof s==='string'&&s.trim()!==''&&Number.isFinite(Number(s));}
 function headerLike(values){
   return values.length>=MIN_SAMPLES &&
     values.slice(0,Math.min(values.length-1,20)).every((x,i)=>x===String(i)||x===String(i+1));
 }
 function inspect(prelude){
   const lines=String(prelude||'').replace(/^\uFEFF/,'').split(/\r?\n/).filter(x=>x.trim());
   if(lines.length<2)return {kind:'not_matrix'};
   let first,second;
   try{first=cells(lines[0]);second=cells(lines[1]);}catch(e){return {kind:'not_matrix'};}
   if(first.length<MIN_SAMPLES||first.length!==second.length)return {kind:'not_matrix'};
   const head=headerLike(first),dataset= head ? second : first;
   if(dataset.slice(0,-1).some(x=>!numeric(x))||(!numeric(dataset[dataset.length-1]) && !dataset[dataset.length-1]))
     return {kind:'not_matrix'};
   // Never assume a categorical value is a waveform. User chooses label exclusion.
   return {kind:'matrix',fields:first.length,hasHeader:head,suggestLabel:[141,188].includes(first.length)};
 }
 function parseRow(line,excludeLast){
   const values=cells(line);
   const fields=excludeLast?values.slice(0,-1):values;
   if(fields.length<MIN_SAMPLES)throw Error('ECG preview needs at least '+MIN_SAMPLES+' ordered sample values');
   if(fields.some(x=>!numeric(x)))throw Error('Row has nonnumeric/blank samples. If the last field is a class label, check Exclude last label column.');
   return fields.map(Number);
 }
 function rowLines(csvText,hasHeader){
   if(typeof csvText!=='string'||csvText.length>8_000_000)throw Error('CSV exceeds the 8 MB text limit');
   const lines=csvText.replace(/^\uFEFF/,'').split(/\r?\n/).filter(x=>x.trim());
   if(hasHeader)lines.shift();
   if(!lines.length||lines.length>MAX_ROWS)throw Error('Row count must be between 1 and '+MAX_ROWS);
   return lines;
 }
 root.WaveAssureECGMatrix=Object.freeze({inspect,cells,parseRow,rowLines,MAX_ROWS});
})(typeof window==='undefined'?globalThis:window);
