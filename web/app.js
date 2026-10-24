'use strict';
let current = null;
let researchModelAvailable = false;
let recordRequestSequence = 0;
let windowRequestSequence = 0;
const $ = id => document.getElementById(id);
const text = (id, value) => { $(id).textContent = String(value); };
const toast = msg => { const el=$('toast'); el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),4200); };
async function request(url, options={}) {
  const response=await fetch(url,{...options,headers:{'Accept':'application/json',...(options.body?{'Content-Type':'application/json'}:{}),...(options.headers||{})}});
  let data=await response.json().catch(()=>({}));
  if(!response.ok) throw Error(typeof data.detail==='string'?data.detail:'Request failed ('+response.status+')');
  return data;
}
function setSection(section){
  for(const name of ['workbench','pilot','records','assurance'])$('section-'+name).classList.toggle('hidden',name!==section);
  document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('active',el.dataset.go===section));
  text('crumb',section.toUpperCase());
  if(section==='records')reloadRecords();
  if(section==='pilot')renderPilot();
  if(section==='assurance')loadAudit();
}
const el=(tag,cls,textValue)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(textValue!==undefined)node.textContent=textValue;return node;};
async function loadRecord(id){
 const sequence = ++recordRequestSequence;
 ++windowRequestSequence;
 try{
  const loaded=await request('/api/records/'+encodeURIComponent(id));
  if(sequence!==recordRequestSequence)return false;
  current=loaded;
  const r=current, name=r.metadata.title;
  text('metricRecord',name.length>22?name.substring(0,21)+'…':name);
  text('metricOrigin',r.metadata.parent_id?'Derived fault experiment · not an expert-labelled recording':r.metadata.origin==='synthetic'?'Synthetic educational data':r.metadata.origin==='wfdb_research'?'Local WFDB • dataset label (not AI): '+r.reference_label:'Unverified research recording');
  text('metricHz',r.sampling_hz+' Hz');
  text('metricQc',r.analysis.status==='TECHNICAL_CHECKS_PASSED'?'No flags*':'Flags found');
  text('waveformSubtitle',r.full_sample_count.toLocaleString()+' samples per channel · '+r.analysis.duration_s+' s');
  text('sourcePill',r.metadata.parent_id?'DERIVED FAULT · RESEARCH':r.metadata.origin==='synthetic'?'SYNTHETIC':r.metadata.origin==='wfdb_research'?'LOCAL WFDB · RESEARCH':'UNVERIFIED');
  $('downloadReport').disabled=false;$('printReport').disabled=false;$('injectBtn').disabled=false;
  $('assessBtn').disabled= !(researchModelAvailable && r.metadata.origin==='wfdb_research' && !r.metadata.parent_id);
  text('assessmentResult','No research inference run for this selection.');
  const channelSelect=$('faultChannel');channelSelect.replaceChildren();
  r.waveforms.forEach(w=>{const opt=el('option','',w.name||w.kind);opt.value=w.name||w.kind;channelSelect.append(opt)});
  const container=$('plots');container.replaceChildren();
  for(const w of r.waveforms){const wrap=el('div','plot');const info=el('div','plot-info');info.append(el('strong','',w.name||w.kind),el('small','',w.unit+' · sampled preview'));wrap.append(info);const canvas=el('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label',(w.name||w.kind)+' signal preview');wrap.append(canvas);container.append(wrap);draw(canvas,w)}
  const isWFDB=r.metadata.origin==='wfdb_research'; $('windowTools').classList.toggle('hidden',!isWFDB);
  if(isWFDB){ $('windowSeconds').value='30'; $('windowStart').max=Math.max(0,Math.floor(r.analysis.duration_s-10)); $('windowStart').value=Math.min(285,Number($('windowStart').max)); text('windowStartValue',$('windowStart').value+' s'); }
  showQuality(r.analysis.quality_checks, r.metadata.origin);
  loadEvidence(id);
  if(window.innerWidth<700)window.scrollTo({top:0,behavior:document.documentElement.dataset.motion==='on'?'smooth':'instant'});
  return true;
 }catch(e){if(sequence===recordRequestSequence)toast(e.message);return false}
}
function draw(canvas,w){
 const dpr=window.devicePixelRatio||1;const bounds=canvas.getBoundingClientRect();const width=Math.max(260,bounds.width);const height=126;
 canvas.width=Math.floor(width*dpr);canvas.height=Math.floor(height*dpr);
 const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
 const pad={left:13,right:10,top:8,bottom:13};const H=height-pad.top-pad.bottom;const W=width-pad.left-pad.right;
 const palette=getComputedStyle(document.documentElement);const colors={ECG:palette.getPropertyValue('--wave-ecg').trim(),PPG:palette.getPropertyValue('--wave-ppg').trim(),ABP:palette.getPropertyValue('--wave-abp').trim()};
 ctx.strokeStyle=palette.getPropertyValue('--grid').trim();ctx.lineWidth=1;
 for(let j=0;j<5;j++){const y=pad.top+j*H/4;ctx.beginPath();ctx.moveTo(pad.left,y);ctx.lineTo(width-pad.right,y);ctx.stroke()}
 for(let j=0;j<9;j++){const x=pad.left+j*W/8;ctx.beginPath();ctx.moveTo(x,pad.top);ctx.lineTo(x,height-pad.bottom);ctx.stroke()}
 const valid=w.values.filter(x=>x!==null&&Number.isFinite(x));if(!valid.length)return;
 let min=Math.min(...valid),max=Math.max(...valid);const range=Math.max(1e-6,max-min);min-=range*.1;max+=range*.1;
 const tmin=w.t[0]||0;const tmax=w.t[w.t.length-1]||1;const trange=Math.max(.001,tmax-tmin);ctx.strokeStyle=colors[w.kind]||colors.ECG;ctx.lineWidth=1.4;ctx.lineJoin='round';ctx.beginPath();let started=false;
 for(let i=0;i<w.values.length;i++){const v=w.values[i];if(v===null||!Number.isFinite(v)){started=false;continue}const x=pad.left+(w.t[i]-tmin)/trange*W,y=pad.top+(max-v)/(max-min)*H;if(!started){ctx.moveTo(x,y);started=true}else{ctx.lineTo(x,y)}}ctx.stroke();
 ctx.font='10px system-ui';ctx.fillStyle=palette.getPropertyValue('--muted').trim();ctx.fillText(tmin.toFixed(1)+' s',pad.left,height-1);ctx.fillText(tmax.toFixed(1)+' s',width-55,height-1);
 if(current && current.metadata.origin==='wfdb_research' && tmin<=300 && tmax>=300){const mark=pad.left+(300-tmin)/trange*W;ctx.beginPath();ctx.setLineDash([4,3]);ctx.strokeStyle=palette.getPropertyValue('--orange').trim();ctx.moveTo(mark,pad.top);ctx.lineTo(mark,height-pad.bottom);ctx.stroke();ctx.setLineDash([]);}
}
function showQuality(channels, origin){
 const cont=$('quality');cont.replaceChildren();
 for(const q of channels){
  const row=el('div','quality-row'),title=el('div','quality-title');title.append(el('b','',q.name||q.kind));
  const flag=el('span','tag '+(q.quality==='passes_technical_checks'?'':'review'),q.quality==='passes_technical_checks'?'No flags':'Attention');title.append(flag);row.append(title);
  const grid=el('div','quality-grid');
  const values=[['Missing',q.missing_pct+'%'],['Signal span',q.span+' '+q.unit],['Std deviation',q.stddev],['ECG rate heuristic', origin==='wfdb_research'?'Withheld: unvalidated':(q.estimated_bpm===null?'Not available':q.estimated_bpm+' BPM*')]];
  for(const pair of values){const cell=el('div');cell.append(el('small','',pair[0]),el('strong','',pair[1]));grid.append(cell)}row.append(grid);
  for(const reason of q.reasons)row.append(el('div','quality-reason','• '+reason));
  cont.append(row);
 }
 cont.append(el('p','note','* Prototype research checks only. An absence of flags does not verify clinical quality or normal physiology; ECG rate heuristic is withheld on real recordings.'));
}
async function loadEvidence(id){
 const panel=$('evidenceContent'); panel.replaceChildren();panel.append(el('p','evidence-note','Loading measured evidence…'));
 try {
  const r=await request('/api/records/'+encodeURIComponent(id)+'/evidence');
  if(!current||current.metadata.id!==id)return;
  panel.replaceChildren();
  const display=[
   ['Data provenance', r.data_class==='IMPORTED_WFDB_RESEARCH'?'Local WFDB research recording':r.data_class==='SYNTHETIC'?'Synthetic educational example':r.data_class==='DERIVED_FAULT_EXPERIMENT'?'Artificially modified copy of a source record':'Unverified CSV input'],
   ['Dataset reference (not AI)',r.reference_annotation.label==='Unlabeled'?'Not available':r.reference_annotation.label+' VT alarm · dataset annotation only'],
   ['Software diagnosis','NOT PERFORMED'],
   ['Original source authenticity','Not independently verified against the official dataset SHA-256 manifest'],
  ];
  const grid=el('div','evidence-facts');
  for(const [name,value] of display){const cell=el('div','evidence-fact');cell.append(el('small','',name),el('strong','',value));grid.append(cell)}
  panel.append(grid);
  const pre=r.descriptive_measurements.pre_alarm_30s;
  if(pre){
   const heading=el('h3','','Measured 30 seconds BEFORE alarm (270–300 s)');panel.append(heading);
   const table=el('table','evidence-table');
   const head=el('tr');for(const x of ['Signal','Measured samples','Missing samples','Mean','Unit'])head.append(el('th','',x));table.append(head);
   for(const c of pre.channels){const tr=el('tr');for(const v of [c.channel,c.valid_samples,c.missing_samples,c.mean===null?'Not available':c.mean,c.unit])tr.append(el('td','',String(v)));table.append(tr)}
   const wrap=el('div','evidence-table-scroll');wrap.append(table);panel.append(wrap);
  }
  panel.append(el('p','evidence-note','These are descriptive values from the imported samples. They do not show whether a patient is safe, whether VT occurred, or whether alarm suppression is appropriate.')); 
 }catch(error){panel.replaceChildren();panel.append(el('p','evidence-note','Evidence calculation unavailable: '+error.message));}
}
async function reloadRecords(){
 try{const data=await request('/api/records');text('recordCount',data.items.length);const list=$('recordList');list.replaceChildren();if(!data.items.length){list.append(el('div','empty','No research records yet.'));return}
 for(const r of data.items){const item=el('div','record-item');const left=el('div','r-main');left.append(el('strong','',r.title),el('small','',r.origin+' · '+new Date(r.created_at).toLocaleString()+(r.parent_id?' · derived from '+r.parent_id.slice(0,8):'')));const btn=el('button','','Open →');btn.addEventListener('click',()=>{setSection('workbench');loadRecord(r.id)});item.append(left,btn);list.append(item)}}catch(e){toast(e.message)}
}
async function loadAudit(){
 try{const [audit,req]=await Promise.all([request('/api/audit'),request('/api/requirements')]);const v=audit.verification;text('auditBadge',v.ok?'CHAIN INTACT':'CHECK FAILED');
 text('auditSummary',v.ok?v.events_checked+' hash-linked event(s) verified. This is not a digital signature or externally secured audit log.':'Audit chain verification failed: '+(v.warning||'Corrupted audit history')+'. New writes are blocked.');
 const container=$('auditEvents');container.replaceChildren();audit.events.slice(0,20).forEach(a=>{const node=el('div','audit-entry');node.append(el('strong','',a.event+' · '+a.object_id.slice(0,8)),el('span','',new Date(a.timestamp).toLocaleString()+' · '+a.entry_hash.slice(0,18)+'…'));container.append(node)});
 const list=$('requirements');list.replaceChildren();req.requirements.forEach(r=>{const row=el('div','req');row.append(el('code','',r.id),el('span','',r.description));list.append(row)});
 }catch(e){toast(e.message)}
}
async function createDemo(kind){try{const d=await request('/api/demo?kind='+encodeURIComponent(kind),{method:'POST'});if(await loadRecord(d.id))toast('Synthetic recording created.');await reloadRecords()}catch(e){toast(e.message)}}
async function createFault(){if(!current)return;try{const fault={kind:$('faultType').value,target:$('faultChannel').value,severity:Number($('faultSeverity').value)};
 const d=await request('/api/records/'+current.metadata.id+'/fault',{method:'POST',body:JSON.stringify(fault)});if(await loadRecord(d.id))toast('Fault injected; original recording preserved.');await reloadRecords()}catch(e){toast(e.message)}}
async function importCSV(file){if(!file)return;try{if(file.size>8_000_000)throw Error('CSV exceeds the 8 MB limit.');const csv_text=await file.text();const d=await request('/api/import-csv',{method:'POST',body:JSON.stringify({title:file.name.slice(0,64),csv_text})});if(await loadRecord(d.id))toast('CSV imported as unverified research data.');await reloadRecords()}catch(e){toast('Import error: '+e.message)}finally{$('csvFile').value=''}}
async function importWFDB(){const path=$('wfdbPath').value.trim();if(!path)return toast('Enter a relative WFDB record path');
 $('importWFDB').disabled=true;
 try{const d=await request('/api/import-wfdb',{method:'POST',body:JSON.stringify({record_path:path})});if(await loadRecord(d.id))toast('Real WFDB recording imported. Reference label is not AI output.');await reloadRecords()}catch(e){toast('WFDB import: '+e.message)}finally{$('importWFDB').disabled=false}}
async function refreshWindow(){if(!current||current.metadata.origin!=='wfdb_research')return;
 const win=Number($('windowSeconds').value);const start=Math.min(Number($('windowStart').value),Math.max(0,current.analysis.duration_s-win));
 const id=current.metadata.id, seq=++windowRequestSequence;
 text('windowStartValue',start+' s');try{const r=await request('/api/records/'+encodeURIComponent(id)+'/preview?start_s='+start+'&window_s='+win);
 if(!current||current.metadata.id!==id||seq!==windowRequestSequence)return;
 current.waveforms=r.waveforms;
 const cvs=document.querySelectorAll('.plot canvas');r.waveforms.forEach((w,i)=>{if(cvs[i])draw(cvs[i],w)});}catch(e){toast(e.message)}}
function downloadReport(){if(!current)return;window.location.href='/api/records/'+encodeURIComponent(current.metadata.id)+'/report'}
for(const item of document.querySelectorAll('.nav'))item.addEventListener('click',()=>setSection(item.dataset.go));
for(const item of document.querySelectorAll('[data-demo]'))item.addEventListener('click',()=>createDemo(item.dataset.demo));
$('injectBtn').addEventListener('click',createFault);$('importWFDB').addEventListener('click',importWFDB);$('windowStart').addEventListener('change',refreshWindow);$('windowSeconds').addEventListener('change',()=>{const win=Number($('windowSeconds').value);$('windowStart').max=Math.max(0,Math.floor(current.analysis.duration_s-win));$('windowStart').value=Math.min(Number($('windowStart').value),Number($('windowStart').max));refreshWindow()});$('csvFile').addEventListener('change',event=>importCSV(event.target.files[0]));$('refreshAudit').addEventListener('click',loadAudit);$('downloadReport').addEventListener('click',downloadReport);$('printReport').addEventListener('click',()=>{if(current)window.open('/api/records/'+encodeURIComponent(current.metadata.id)+'/report.html','_blank','noopener')});
$('faultSeverity').addEventListener('input',()=>text('severityValue',$('faultSeverity').value));window.addEventListener('resize',()=>{if(current)current.waveforms.forEach((w,i)=>{const canvases=document.querySelectorAll('.plot canvas');if(canvases[i])draw(canvases[i],w)})});
reloadRecords();

request('/api/wfdb/config').then(r=>text('wfdbRootInfo',r.configured?'Dataset folder: '+r.root:'Configure WAVEASSURE_WFDB_ROOT and restart the server')).catch(()=>{});

async function loadResearchModelStatus(){
  try {
    const status=await request('/api/research-model/status');
    researchModelAvailable=Boolean(status.available);
    text('modelState',researchModelAvailable?'Research model loaded':'Not trained');
    text('modelDetail',researchModelAvailable?'Locally trained retrospective model available. Results have no clinical use.':'No trained model is installed. Use scripts/train-vtac-windows.bat after enough valid labelled True and False events exist in official train/validation/test partitions.');
    $('assessBtn').disabled= !(researchModelAvailable && current && current.metadata.origin==='wfdb_research' && !current.metadata.parent_id);
  }catch(err){
    researchModelAvailable=false;text('modelDetail','Model status unavailable: '+err.message);
  }
}
$('assessBtn').addEventListener('click',async()=>{
  if(!current || !researchModelAvailable)return;
  $('assessBtn').disabled=true;
  try {
    const r=await request('/api/records/'+encodeURIComponent(current.metadata.id)+'/research-assessment',{method:'POST'});
    const a=r.assessment;
    text('assessmentResult','RESEARCH ONLY · '+a.exploratory_classification+'\nUnvalidated research score: '+(100*a.research_probability_true_vt).toFixed(2)+'% (not a clinical probability)\nExpert reference label (separate): '+r.reference_label+'\nModel SHA-256: '+a.model_sha256.slice(0,16)+'…');
  }catch(e){text('assessmentResult','Could not assess record: '+e.message)}
  finally{$('assessBtn').disabled=false}
});
loadResearchModelStatus();

// Local retrospective usability pilot. Deliberately NOT a medical trial.
let pilotSession=null, pilotCase=null, pilotWaveforms=[];
function renderPilot(){
  if(!pilotSession){text('pilotProgress','No session started');text('pilotSessionId','—');$('pilotFinalize').disabled=true;$('pilotExport').disabled=true;return}
  text('pilotProgress',pilotSession.completed_cases+' / '+pilotSession.total_cases+' reviewed · '+(pilotSession.completed?'Finalized':'Local session'));text('pilotSessionId',pilotSession.id);
  $('pilotFinalize').disabled=pilotSession.completed||pilotSession.completed_cases!==pilotSession.total_cases;
  $('pilotExport').disabled=!pilotSession.completed;
  const next=pilotSession.cases.find(c=>!c.reviewed);
  if(!next){pilotCase=null;pilotWaveforms=[];text('pilotCaseStatus',pilotSession.completed?'Session finalized. Download report to view dataset reference comparisons.':'Every case reviewed. Finalize to unlock comparison report.');$('pilotSubmit').disabled=true;$('pilotPlots').replaceChildren();return}
  showPilotCase(next.record_id);
}
async function showPilotCase(id){
  try {
    const result=await request('/api/pilot/sessions/'+pilotSession.id+'/cases/'+id);
    pilotCase=id;pilotWaveforms=result.waveforms;text('pilotCaseStatus','Case '+result.case_number+' / '+pilotSession.total_cases+' · 285–300 seconds · dataset label masked');
    $('pilotPlots').replaceChildren();
    for(const w of result.waveforms){
      const wrap=el('div','plot'),info=el('div','plot-info');info.append(el('strong','',w.name||w.kind),el('small','',w.unit+' · pre-alarm waveform'));
      wrap.append(info);const canvas=el('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label',(w.name||w.kind)+' pre-alarm waveform');wrap.append(canvas);$('pilotPlots').append(wrap);draw(canvas,w);
    }
    $('pilotSubmit').disabled=false;
  }catch(err){pilotCase=null;$('pilotSubmit').disabled=true;text('pilotMessage','Unable to load case: '+err.message)}
}
$('pilotCreate').addEventListener('click',async()=>{
  const code=$('reviewerCode').value.trim();
  try {pilotSession=await request('/api/pilot/sessions',{method:'POST',body:JSON.stringify({reviewer_code:code})});text('pilotMessage','Reviewer session created. Never use this tool for patient care.');renderPilot()}
  catch(err){text('pilotMessage','Cannot start: '+err.message)}
});
$('pilotResume').addEventListener('click',async()=>{
 const id=$('pilotResumeId').value.trim();
 if(!/^[0-9a-f]{32}$/.test(id)){text('pilotMessage','Enter a valid 32-character local session ID.');return}
 try{pilotSession=await request('/api/pilot/sessions/'+id);text('pilotMessage','Existing local session loaded.');renderPilot()}
 catch(err){text('pilotMessage','Cannot load session: '+err.message)}
});
$('pilotSubmit').addEventListener('click',async()=>{
  if(!pilotCase||!pilotSession)return;
  $('pilotSubmit').disabled=true;
  const payload={record_id:pilotCase,decision:$('pilotDecision').value,confidence:$('pilotConfidence').value,
       quality:$('pilotQuality').value,notes:$('pilotNotes').value};
  try {
    pilotSession=await request('/api/pilot/sessions/'+pilotSession.id+'/responses',{method:'POST',body:JSON.stringify(payload)});
    $('pilotNotes').value='';text('pilotMessage','Review saved and locked; no dataset label disclosed.');renderPilot();
  }catch(err){text('pilotMessage','Review failed: '+err.message);$('pilotSubmit').disabled=false}
});
$('pilotFinalize').addEventListener('click',async()=>{
  if(!pilotSession)return;
  try {pilotSession=await request('/api/pilot/sessions/'+pilotSession.id+'/finalize',{method:'POST'});text('pilotMessage','Session finalized. Dataset reference comparison is now available in report.');renderPilot()}
  catch(err){text('pilotMessage','Cannot finalize: '+err.message)}
});
$('pilotExport').addEventListener('click',async()=>{
 if(!pilotSession||!pilotSession.completed)return;
 try {const r=await request('/api/pilot/sessions/'+pilotSession.id+'/export');const blob=new Blob([JSON.stringify(r,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='waveassure-review-'+pilotSession.id.slice(0,8)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
 catch(err){text('pilotMessage','Could not export: '+err.message)}
});

// Appearance affects presentation only; waveform samples and computed metrics remain unchanged.
window.addEventListener('waveassure:appearance',()=>{
 if(current){const plots=document.querySelectorAll('#plots .plot canvas');current.waveforms.forEach((w,i)=>{if(plots[i])draw(plots[i],w);});}
 if(pilotSession && pilotCase){const canvases=document.querySelectorAll('#pilotPlots .plot canvas');pilotWaveforms.forEach((w,i)=>{if(canvases[i])draw(canvases[i],w);});}
});
