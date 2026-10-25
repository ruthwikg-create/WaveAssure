/* Browser-local ECG segment inspection. Never uploads or stores a beat-matrix as an
   authentic continuous ECG recording; never produces a diagnosis or event time. */
(function(root){
 'use strict';
 const $=id=>document.getElementById(id);
 let file=null,layout=null,loadedLines=null,lastSamples=null;
 function status(message){$('ecgMatrixStatus').textContent=message;}
 function ready(){ $('ecgMatrixPreview').disabled=!file||!$('ecgMatrixConfirm').checked; }
 function reset(){
   file=null;layout=null;loadedLines=null;lastSamples=null;
   $('ecgMatrixPanel').classList.add('hidden');
   $('ecgMatrixChart').classList.add('hidden');
   $('ecgMatrixConfirm').checked=false;
   $('ecgMatrixPreview').disabled=true;
   $('ecgMatrixRow').value='1';
   $('ecgMatrixRow').removeAttribute('max');
   status('');
 }
 function show(nextFile,info){
   reset();file=nextFile;layout=info;
   $('ecgMatrixPanel').classList.remove('hidden');
   $('ecgMatrixHeader').value=info.hasHeader?'yes':'no';
   $('ecgMatrixLabel').checked=info.suggestLabel;
   $('ecgMatrixDetails').textContent=nextFile.name+' · '+info.fields+
     ' fields per row (candidate ECG sample matrix). Check layout and class-label setting.';
   status('Confirm the dataset structure and click Preview selected ECG segment.');
 }
 function color(name,fallback){return getComputedStyle(document.documentElement).getPropertyValue(name).trim()||fallback;}
 function chart(samples){
   const canvas=$('ecgMatrixCanvas');const rect=canvas.getBoundingClientRect();
   const width=Math.max(260,rect.width||600),height=Math.max(170,rect.height||180);
   const ratio=Math.min(2,root.devicePixelRatio||1);
   canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);
   const ctx=canvas.getContext('2d');if(!ctx)return;
   ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,width,height);
   const left=42,right=16,top=14,bottom=27,plotWidth=width-left-right,plotHeight=height-top-bottom;
   const lo=Math.min(...samples),hi=Math.max(...samples);
   const spread=hi-lo||Math.max(1,Math.abs(hi));
   const low=lo-spread*0.08,high=hi+spread*0.08;
   ctx.strokeStyle=color('--line','#899');ctx.lineWidth=1;
   ctx.beginPath();ctx.moveTo(left,top);ctx.lineTo(left,height-bottom);ctx.lineTo(width-right,height-bottom);ctx.stroke();
   ctx.fillStyle=color('--muted','#566');ctx.font='11px sans-serif';
   ctx.textAlign='right';ctx.fillText(hi.toPrecision(3),left-7,top+5);
   ctx.fillText(lo.toPrecision(3),left-7,height-bottom);
   ctx.textAlign='left';ctx.fillText('0',left,height-7);
   ctx.textAlign='right';ctx.fillText(String(samples.length-1),width-right,height-7);
   ctx.strokeStyle=color('--mint','#087e70');ctx.lineWidth=1.6;ctx.beginPath();
   for(let i=0;i<samples.length;i++){
     const x=left+i/(samples.length-1)*plotWidth;
     const y=top+(high-samples[i])/(high-low)*plotHeight;
     if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
   }
   ctx.stroke();
 }
 async function preview(){
   if(!file||!$('ecgMatrixConfirm').checked){status('Confirm the ECG segment structure first.');return}
   const button=$('ecgMatrixPreview');button.disabled=true;
   try{
     const header=$('ecgMatrixHeader').value==='yes';
     if(!loadedLines||loadedLines.hasHeader!==header){
       const content=await file.text();
       loadedLines={hasHeader:header,lines:root.WaveAssureECGMatrix.rowLines(content,header)};
     }
     const lines=loadedLines.lines;const row=Number($('ecgMatrixRow').value);
     if(!Number.isSafeInteger(row)||row<1||row>lines.length)
       throw Error('Row number must be between 1 and '+lines.length+'.');
     const samples=root.WaveAssureECGMatrix.parseRow(lines[row-1],$('ecgMatrixLabel').checked);
     if(samples.length!==layout.fields-Number($('ecgMatrixLabel').checked))
       throw Error('Row column count is inconsistent with the file header/first row.');
     lastSamples=samples;
     $('ecgMatrixRow').max=String(lines.length);
     $('ecgMatrixPlotTitle').textContent='ECG sample segment '+row+' of '+lines.length;
     const min=Math.min(...samples),max=Math.max(...samples);
     $('ecgMatrixStats').textContent=samples.length+' finite ordered values · minimum '+
       min.toPrecision(4)+' · maximum '+max.toPrecision(4)+
       ' (original unspecified amplitude units). No sampling frequency, duration, alarm or class meaning inferred.';
     $('ecgMatrixChart').classList.remove('hidden');chart(samples);
     status('Preview only. Nothing was imported as a clinical recording. Use the row number to view another ECG segment.');
   }catch(error){lastSamples=null;$('ecgMatrixChart').classList.add('hidden');status('Cannot preview row: '+error.message)}
   finally{ready()}
 }
 $('ecgMatrixConfirm').addEventListener('change',ready);
 for(const id of ['ecgMatrixHeader','ecgMatrixLabel','ecgMatrixRow']){
   $(id).addEventListener('change',()=>{
     if(id==='ecgMatrixHeader')loadedLines=null;
     lastSamples=null;$('ecgMatrixChart').classList.add('hidden');
     status('Layout or segment changed. Click Preview selected ECG segment.');
   });
 }
 $('ecgMatrixPreview').addEventListener('click',preview);
 root.addEventListener('resize',()=>{if(lastSamples&& !$('ecgMatrixChart').classList.contains('hidden'))chart(lastSamples)});
 root.WaveAssureECGPreview=Object.freeze({show,reset});
})(window);
