'use strict';
let current = null;
let researchModelAvailable = false;
let recordRequestSequence = 0;
let windowRequestSequence = 0;
const replay = {running:false, frame:0, at:0, previous:0, lastMs:0, lastFetchMs:0, pending:false};
let selectedCSV=null;
let selectedWFDB=null;
let fileSelectionSequence=0;
const clockTime = t => { const v=Math.max(0,Number(t)||0); return String(Math.floor(v/60)).padStart(2,'0')+':'+String(Math.floor(v%60)).padStart(2,'0')+'.'+Math.floor((v%1)*10); };
function annotatedAlarm(){
 if(!current || current.metadata.parent_id)return null;
 if(current.alarm_time_s !== null && Number.isFinite(current.alarm_time_s))return current.alarm_time_s;
 // Older stored VTaC event records were saved without an explicit timestamp.
 if(current.metadata.origin==='wfdb_research' && ['True','False'].includes(current.reference_label)
    && String(current.source_reference||'').includes('VTaC') && current.analysis.duration_s>=300)return 300;
 return null;
}
function replayLimit(){return Math.max(0,(current?.analysis.duration_s||0)-Number($('windowSeconds').value));}
function pauseReplay(){replay.running=false;cancelAnimationFrame(replay.frame);replay.frame=0;replay.pending=false;$('replayToggle').textContent='▶ Play recording';$('replayToggle').setAttribute('aria-pressed','false');}
function simulatedTone(){
 if(!$('alarmTone').checked)return;
 try { const AudioContextClass=window.AudioContext||window.webkitAudioContext;if(!AudioContextClass)return;
 const ac=new AudioContextClass(),osc=ac.createOscillator(),gain=ac.createGain();
 osc.type='sine';osc.frequency.value=520;gain.gain.setValueAtTime(0.0001,ac.currentTime);
 gain.gain.exponentialRampToValueAtTime(0.045,ac.currentTime+0.01);
 gain.gain.exponentialRampToValueAtTime(0.0001,ac.currentTime+0.16);
 osc.connect(gain);gain.connect(ac.destination);osc.start();osc.stop(ac.currentTime+0.18);
 osc.onended=()=>ac.close();
 }catch(_){ /* Audio preview is optional and not part of the source recording. */ }
}
function replayStep(now){
 if(!replay.running||!current)return;
 if(document.hidden){pauseReplay();return;}
 const dt=replay.lastMs?Math.min(0.25,(now-replay.lastMs)/1000):0;
 replay.lastMs=now;
 const speed=Number($('replaySpeed').value)||1;
 const before=replay.at + Number($('windowSeconds').value)/2;
 replay.at=Math.min(replayLimit(),replay.at+Math.max(0,dt)*speed);
 const after=replay.at + Number($('windowSeconds').value)/2;
 const alarm=annotatedAlarm();
 if(alarm!==null && before<alarm && after>=alarm)simulatedTone();
 $('windowStart').value=String(replay.at);
 text('windowStartValue',clockTime(replay.at));text('replayClock',clockTime(after));
 if(!replay.pending && now-replay.lastFetchMs>=180){
   replay.lastFetchMs=now;replay.pending=true;
   refreshWindow(replay.at).finally(()=>{replay.pending=false});
 }
 if(replay.at >= replayLimit()){pauseReplay();return;}
 replay.frame=requestAnimationFrame(replayStep);
}
function toggleReplay(){
 if(!current)return;
 if(replay.running){pauseReplay();return;}
 if(replay.at >= replayLimit())replay.at=0;
 replay.running=true;replay.lastMs=0;replay.lastFetchMs=0;
 $('replayToggle').textContent='Ⅱ Pause recording';$('replayToggle').setAttribute('aria-pressed','true');
 replay.frame=requestAnimationFrame(replayStep);
}
function showAlarmExplanation() {
 const detail=$('alarmExplanation');
 const alarm=annotatedAlarm();
 const interpretation=window.WaveAssureAlarmEvent.explain(current,alarm);
 detail.replaceChildren();
 const title=el('h3','',interpretation.status);
 detail.append(title);
 if(alarm!==null)detail.append(el('p','alarm-explanation-time','Recorded marker: '+clockTime(alarm)+' ('+alarm.toFixed(3)+' seconds from recording start).'));
 for(const [label,value] of [
  ['Recorded reference',interpretation.classification],
  ['Meaning',interpretation.reason],
  ['Evidence source',interpretation.source],
  ['Safety limit',interpretation.disclaimer]
 ]) {
  const row=el('div','alarm-explanation-row');row.append(el('strong','',label),el('p','',value));detail.append(row);
 }
 detail.classList.remove('hidden');
 $('explainAlarm').setAttribute('aria-expanded','true');
 detail.focus({preventScroll:true});
}
function alarmMarkerPosition(canvas,w) {
 const alarm=annotatedAlarm();
 if(alarm===null || !w || !w.t || w.t.length<2)return null;
 const tmin=w.t[0],tmax=w.t[w.t.length-1];
 if(alarm<tmin || alarm>tmax)return null;
 const width=Math.max(260,canvas.getBoundingClientRect().width);
 return 13+(alarm-tmin)/Math.max(.001,tmax-tmin)*(width-23);
}
function onAlarmCanvasClick(event,canvas,w){
 const x=alarmMarkerPosition(canvas,w);
 if(x===null)return;
 const local=event.clientX-canvas.getBoundingClientRect().left;
 if(Math.abs(local-x)<=24)showAlarmExplanation();
}
function renderAlarm(){
 const alarm=annotatedAlarm();
 $('jumpAlarm').disabled=(alarm===null);
 $('explainAlarm').disabled=!current;
 if(alarm===null){text('alarmDetail','No alarm timestamp is documented for this recording. WaveAssure cannot infer the original buzzer time.');return;}
 const source=current.alarm_time_source==='dataset_annotation'?'Local VTaC label file (not independently authenticated)':
  current.alarm_time_source==='user_annotation_unverified'?'User-entered timestamp (unverified)':'Legacy VTaC dataset reference';
 text('alarmDetail','Alarm marker at '+clockTime(alarm)+' ('+alarm.toFixed(3)+' s) · '+source+'. No original monitor audio was imported.');
}

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
  if(section!=='workbench')pauseReplay();
  for(const name of ['workbench','pilot','records','assurance'])$('section-'+name).classList.toggle('hidden',name!==section);
  document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('active',el.dataset.go===section));
  text('crumb',{workbench:'Workbench',pilot:'Review practice',records:'Records',assurance:'Assurance log'}[section] || section);
  document.querySelectorAll('.nav').forEach(button => button.setAttribute('aria-current', button.dataset.go===section ? 'page' : 'false'));
  if(section==='records')reloadRecords();
  if(section==='pilot')renderPilot();
  if(section==='assurance')loadAudit();
}
const el=(tag,cls,textValue)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(textValue!==undefined)node.textContent=textValue;return node;};
async function loadRecord(id){
 pauseReplay();
 const sequence = ++recordRequestSequence;
 ++windowRequestSequence;
 try{
  const loaded=await request('/api/records/'+encodeURIComponent(id));
  if(sequence!==recordRequestSequence)return false;
  current=loaded;
  const r=current, name=r.metadata.title;
  text('metricRecord',name.length>22?name.substring(0,21)+'…':name);
  text('metricOrigin',r.metadata.parent_id?'Derived fault experiment · not an expert-labelled recording':r.metadata.origin==='synthetic'?'Synthetic educational data':r.metadata.origin==='wfdb_research'?(r.reference_label==='Unlabeled'?'Custom WFDB · no verified expert label':'Local WFDB · dataset label (not AI): '+r.reference_label):'Unverified research recording');
  text('metricHz',r.sampling_hz+' Hz');
  text('metricQc',r.analysis.status==='TECHNICAL_CHECKS_PASSED'?'No flags*':'Flags found');
  text('waveformSubtitle',r.full_sample_count.toLocaleString()+' samples per channel · '+r.analysis.duration_s+' s');
  text('sourcePill',r.metadata.parent_id?'DERIVED FAULT · RESEARCH':r.metadata.origin==='synthetic'?'SYNTHETIC':r.metadata.origin==='wfdb_research'?'LOCAL WFDB · RESEARCH':'UNVERIFIED');
  $('downloadReport').disabled=false;$('printReport').disabled=false;$('injectBtn').disabled=false;
  $('assessBtn').disabled= !(researchModelAvailable && r.metadata.origin==='wfdb_research' && !r.metadata.parent_id && ['True','False'].includes(r.reference_label));
  text('assessmentResult','No research inference run for this selection.');
  const channelSelect=$('faultChannel');channelSelect.replaceChildren();
  r.waveforms.forEach(w=>{const opt=el('option','',w.name||w.kind);opt.value=w.name||w.kind;channelSelect.append(opt)});
  $('alarmExplanation').classList.add('hidden');
  $('explainAlarm').setAttribute('aria-expanded','false');
  const container=$('plots');container.replaceChildren();
  for(const w of r.waveforms){const wrap=el('div','plot');const info=el('div','plot-info');info.append(el('strong','',w.name||w.kind),el('small','',w.unit+' · sampled preview'));wrap.append(info);const canvas=el('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label',(w.name||w.kind)+' signal preview');wrap.append(canvas);container.append(wrap);draw(canvas,w);canvas.addEventListener('click',event=>onAlarmCanvasClick(event,canvas,(current?.waveforms||[]).find(s=>s.name===w.name)||w));canvas.addEventListener('mousemove',event=>{const active=(current?.waveforms||[]).find(s=>s.name===w.name)||w;const x=alarmMarkerPosition(canvas,active);canvas.style.cursor=x!==null&&Math.abs(event.clientX-canvas.getBoundingClientRect().left-x)<=24?'pointer':'default';});}
  $('windowTools').classList.remove('hidden');
  const duration=r.analysis.duration_s;
  const win=duration>=30?30:duration>=10?10:duration>=5?5:duration>=2?2:1;
  $('windowSeconds').value=String([1,2,5,10,30,60,360].includes(win)?win:1);
  const max=Math.max(0,duration-Number($('windowSeconds').value));
  const alarm=annotatedAlarm();
  const start=(alarm===null?0:Math.max(0,Math.min(max,alarm-20)));
  $('windowStart').max=String(max); $('windowStart').value=String(start);
  replay.at=start;replay.previous=start;
  text('windowStartValue',clockTime(start));text('replayClock',clockTime(start+Number($('windowSeconds').value)/2));
  renderAlarm();
  showQuality(r.analysis.quality_checks, r.metadata.origin);
  loadEvidence(id);
  refreshWindow(start);
  if(window.innerWidth<700)window.scrollTo({top:0,behavior:document.documentElement.dataset.motion==='on'?'smooth':'instant'});
  return true;
 }catch(e){if(sequence===recordRequestSequence)toast(e.message);return false}
}
function draw(canvas,w, settings={}){
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
 const alarm = settings.hideAlarm ? null : annotatedAlarm();
 if(alarm!==null && tmin<=alarm && tmax>=alarm){
  const mark=pad.left+(alarm-tmin)/trange*W;
  ctx.save();ctx.beginPath();ctx.setLineDash([4,3]);ctx.strokeStyle=palette.getPropertyValue('--orange').trim();ctx.lineWidth=1.5;
  ctx.moveTo(mark,pad.top);ctx.lineTo(mark,height-pad.bottom);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle=palette.getPropertyValue('--orange').trim();ctx.font='bold 10px system-ui';
  ctx.fillText('ALARM '+clockTime(alarm),Math.min(mark+4,width-110),pad.top+11);ctx.restore();
 }
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
   const heading=el('h3','','Measured samples before annotated alarm ('+clockTime(pre.start_s)+'–'+clockTime(pre.end_s)+')');panel.append(heading);
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
function safeCSVHeader(line){
 const result=[];let value='',quoted=false;
 for(let i=0;i<line.length;i++){
  const ch=line[i];if(ch==='"'){
   if(quoted&&line[i+1]==='"'){value+='"';i++;}else quoted=!quoted;
  }else if(ch===','&&!quoted){result.push(value);value='';}else value+=ch;
 }
 if(quoted)throw Error('Unclosed quoted CSV header');result.push(value);return result;
}
const CSV_IDENTIFIER_TOKENS=['patient','subject','name','first_name','last_name','dob','birth',
 'email','phone','address','mrn','medical_record','person_id'];
const CSV_EVENT_TOKENS=new Set(['alert','alarm','flag','status','accuracy','diagnosis',
 'diagnostic','risk','classification','label','warning']);
const CSV_SCALAR_FIELDS=new Set(['heart_rate','heartrate','pulse_rate','spo2',
 'oxygen_saturation','respiration_rate','respiratory_rate','body_temperature','temperature']);
function csvFieldType(header){
 const h=header.trim().toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'');
 if(CSV_IDENTIFIER_TOKENS.some(token=>h.includes(token)))return 'identifier';
 if(CSV_SCALAR_FIELDS.has(h)||h.split('_').some(token=>CSV_EVENT_TOKENS.has(token)))return 'summary';
 if(['time_s','time_ms','time','elapsed_s','elapsed_ms','elapsed_time','timestamp_s',
     'timestamp_ms','timestamp','sample_time','seconds','milliseconds'].includes(h))return 'time';
 if(h.includes('pleth')||h.includes('ppg'))return 'PPG';
 if(h==='abp'||h.startsWith('abp_')||h==='arterial_pressure')return 'ABP';
 if(/^(i|ii|iii|avr|avl|avf|v[1-6]?|ecg.*|lead.*)$/.test(h))return 'ECG';
 return '';
}
function csvColumnGuess(header){
 const type=csvFieldType(header);
 return type==='identifier'||type==='summary'?'':type;
}
function showCSVMapping(file, sequence){
 if(!file)return;
 selectedCSV=file;
 if(file.size>8_000_000){text('datasetSelectionStatus','CSV exceeds 8 MB; choose a smaller recording.');selectedCSV=null;return}
 file.slice(0,8192).text().then(head=>{
   if(sequence!==fileSelectionSequence)return;
   let first=head.replace(/^\uFEFF/,'').split(/\r?\n/)[0];
   const columns=safeCSVHeader(first);
   if(!columns.length||columns.length>60||new Set(columns).size!==columns.length)throw Error('CSV must have unique headers (up to 60)');
   $('csvMapper').classList.remove('hidden');text('csvName',file.name);
   const time=$('csvTimeColumn');time.replaceChildren();
   const emptyTime=el('option','','Choose elapsed time column');emptyTime.value='';time.append(emptyTime);
   const body=$('csvChannels');body.replaceChildren();
   columns.forEach((name,i)=>{
     const op=el('option','',name);op.value=name;time.append(op);
     const row=el('label','csv-channel-row');
     const use=el('input');use.type='checkbox';use.className='channel-use';use.dataset.column=name;
     const guess=csvColumnGuess(name);use.checked=Boolean(guess&&guess!=='time');
     const span=el('span','',name);const select=el('select','channel-kind');
     for(const [kind,unit] of [['ECG','mV'],['PPG','a.u./NU'],['ABP','mmHg']]){const o=el('option','',kind+' ('+unit+')');o.value=kind;select.append(o)}
     const units=el('select','channel-unit');
     const syncUnits=()=>{units.replaceChildren();
       for(const unit of (select.value==='PPG'?['a.u.','NU']:select.value==='ABP'?['mmHg']:['mV'])){
         const option=el('option','',unit);option.value=unit;units.append(option)}
       if(select.value==='PPG'&&name.toLowerCase().includes('pleth'))units.value='NU';
     };
     select.value=guess&&guess!=='time'?guess:'ECG';select.addEventListener('change',syncUnits);syncUnits();
     row.append(use,span,select,units);body.append(row);
   });
   const timeName=columns.find(c=>csvColumnGuess(c)==='time');
   time.value=timeName||'';
   $('csvTimeUnit').value=timeName&&timeName.toLowerCase().includes('ms')?'ms':'s';
   const identifiers=columns.filter(c=>csvFieldType(c)==='identifier');
   const summaries=columns.filter(c=>csvFieldType(c)==='summary');
   const warning=identifiers.length
     ? 'Import blocked: identifying header(s) found: '+identifiers.join(', ')+
       '. Remove identifying columns locally, then choose the cleaned CSV. Patient alert tables cannot be displayed as ECG waveforms.'
     : summaries.length
       ? 'Alert, status and scalar vital-sign fields (including '+summaries.slice(0,3).join(', ')+
         ') are not ECG/PPG/ABP waveform samples. They are excluded. Choose actual time-series waveform columns or use a suitable waveform dataset.'
       : 'Choose a measured waveform and confirm its actual units; no physiological values or alarm labels are inferred.';
   const updateReady=()=>{
     const selected=Array.from(body.querySelectorAll('.channel-use')).filter(box=>box.checked);
     const invalid=selected.filter(box=>['identifier','summary','time'].includes(csvFieldType(box.dataset.column))||
       box.dataset.column===time.value);
     $('importCustomCSV').disabled=Boolean(identifiers.length)||!time.value||!selected.length||
       selected.length>8||invalid.length>0;
     text('csvFormatAdvice',warning+
       (!time.value?' No elapsed-time column was recognized; select one explicitly if present.':'')+
       (invalid.length?' Uncheck non-waveform/elapsed-time columns: '+invalid.map(box=>box.dataset.column).join(', ')+'.':'')+
       (selected.length>8?' Select no more than 8 waveform columns.':''));
   };
   time.addEventListener('change',updateReady);body.addEventListener('change',updateReady);
   updateReady();
 }).catch(e=>{if(sequence===fileSelectionSequence){$('csvMapper').classList.add('hidden');selectedCSV=null;text('datasetSelectionStatus','Cannot read CSV header: '+e.message);}});
}
async function importCSV(){
 if(!selectedCSV)return toast('Choose a CSV file first');
 const button=$('importCustomCSV');button.disabled=true;
 try{
  if(selectedCSV.size>8_000_000)throw Error('CSV exceeds the 8 MB limit');
  const mappings=[];
  for(const row of document.querySelectorAll('.csv-channel-row')){
   if(!row.querySelector('.channel-use').checked)continue;
   const name=row.querySelector('.channel-use').dataset.column;
   const kind=row.querySelector('.channel-kind').value;
   const clean=name.trim().replace(/[^a-zA-Z0-9_+-]/g,'_').slice(0,24);
   const unit=row.querySelector('.channel-unit').value;
   mappings.push({column:name,name:clean||kind,kind,unit});
  }
  if(mappings.length<1||mappings.length>8)throw Error('Select 1 to 8 signal columns');
  if(!$('csvTimeColumn').value)throw Error('Select an elapsed-time column. Patient number and row number are not time.');
  const rawAlarm=$('csvAlarmTime').value.trim();
  const csv_text=await selectedCSV.text();
  const payload={title:selectedCSV.name.slice(0,64),csv_text,
   time_column:$('csvTimeColumn').value,time_unit:$('csvTimeUnit').value,channel_mapping:mappings,
   alarm_time_s:rawAlarm===''?null:Number(rawAlarm)};
  const response=await request('/api/import-csv',{method:'POST',body:JSON.stringify(payload)});
  $('csvMapper').classList.add('hidden');selectedCSV=null;resetUnifiedUpload();
  await loadRecord(response.id);await reloadRecords();toast('Custom research CSV imported. Source and units are unverified.');
 }catch(e){text('csvMapperStatus','Import failed: '+e.message);toast('CSV import: '+e.message)}
 finally{button.disabled=false}
}
function resetUnifiedUpload(){
 ++fileSelectionSequence;
 $('datasetFiles').value='';
 selectedCSV=null;selectedWFDB=null;
 $('csvMapper').classList.add('hidden');$('wfdbPairOptions').classList.add('hidden');
 $('csvAlarmTime').value='';$('wfdbAlarmTime').value='';
 text('datasetSelectionStatus','No recording selected.');
}
function handleDatasetSelection(files){
 const sequence=++fileSelectionSequence;
 selectedCSV=null;selectedWFDB=null;
 $('csvMapper').classList.add('hidden');$('wfdbPairOptions').classList.add('hidden');
 $('csvAlarmTime').value='';$('wfdbAlarmTime').value='';
 text('csvMapperStatus','');text('wfdbImportStatus','');
 const choice=window.WaveAssureDatasetUpload.classify(files);
 if(choice.kind==='invalid'){
   text('datasetSelectionStatus',choice.error);
   return;
 }
 if(choice.kind==='csv'){
   text('datasetSelectionStatus','CSV selected: '+choice.file.name+' — configure columns below.');
   showCSVMapping(choice.file,sequence);
   return;
 }
 selectedWFDB=choice;
 text('datasetSelectionStatus','WFDB pair selected: '+choice.header.name+' + '+choice.data.name+'.');
 text('wfdbPairSummary',choice.header.name+' + '+choice.data.name);
 $('wfdbPairOptions').classList.remove('hidden');
}
async function importWFDBFiles(){
 const pair=selectedWFDB;
 if(!pair)return toast('Select both matching .hea and .dat files in the single upload input');
 const button=$('importWFDBFiles');button.disabled=true;
 try{
  const buffer=new Uint8Array(await pair.data.arrayBuffer());let raw='';
  for(let i=0;i<buffer.length;i+=16384)raw+=String.fromCharCode(...buffer.subarray(i,i+16384));
  const time=$('wfdbAlarmTime').value.trim();
  const response=await request('/api/import-wfdb-files',{method:'POST',body:JSON.stringify({
   header_filename:pair.header.name,header_text:await pair.header.text(),data_filename:pair.data.name,data_base64:btoa(raw),
   alarm_time_s:time===''?null:Number(time)})});
  resetUnifiedUpload();
  await loadRecord(response.id);await reloadRecords();toast('WFDB pair imported with checksums; no verified expert label.');
 }catch(e){text('wfdbImportStatus','Import failed: '+e.message);toast('WFDB import: '+e.message)}finally{button.disabled=false}
}
async function importWFDB(){const path=$('wfdbPath').value.trim();if(!path)return toast('Enter a relative WFDB record path');
 $('importWFDB').disabled=true;
 try{const d=await request('/api/import-wfdb',{method:'POST',body:JSON.stringify({record_path:path})});if(await loadRecord(d.id))toast('Real WFDB recording imported. Reference label is not AI output.');await reloadRecords()}catch(e){toast('WFDB import: '+e.message)}finally{$('importWFDB').disabled=false}}
async function refreshWindow(startOverride=null){
 if(!current)return;
 const win=Number($('windowSeconds').value);
 const maximum=Math.max(0,current.analysis.duration_s-win);
 const wanted=startOverride===null?Number($('windowStart').value):Number(startOverride);
 const start=Math.max(0,Math.min(maximum,wanted));
 const id=current.metadata.id,seq=++windowRequestSequence;
 text('windowStartValue',clockTime(start));
 if(!replay.running)text('replayClock',clockTime(start+win/2));
 try{
  const r=await request('/api/records/'+encodeURIComponent(id)+'/preview?start_s='+start.toFixed(3)+'&window_s='+win);
  if(!current||current.metadata.id!==id||seq!==windowRequestSequence)return;
  current.waveforms=r.waveforms;
  const cvs=document.querySelectorAll('#plots .plot canvas');
  r.waveforms.forEach((w,i)=>{if(cvs[i])draw(cvs[i],w)});
 }catch(e){if(seq===windowRequestSequence)toast('Waveform preview: '+e.message)}
}
function downloadReport(){if(!current)return;window.location.href='/api/records/'+encodeURIComponent(current.metadata.id)+'/report'}
for(const item of document.querySelectorAll('.nav'))item.addEventListener('click',()=>setSection(item.dataset.go));
for(const item of document.querySelectorAll('[data-demo]'))item.addEventListener('click',()=>createDemo(item.dataset.demo));
$('injectBtn').addEventListener('click',createFault);$('importWFDB').addEventListener('click',importWFDB);
$('importWFDBFiles').addEventListener('click',importWFDBFiles);
$('datasetFiles').addEventListener('change',event=>handleDatasetSelection(event.target.files));
$('importCustomCSV').addEventListener('click',importCSV);
$('replayToggle').addEventListener('click',toggleReplay);
$('explainAlarm').addEventListener('click',showAlarmExplanation);
$('windowStart').addEventListener('input',()=>{pauseReplay();replay.at=Number($('windowStart').value);text('windowStartValue',clockTime(replay.at));});
$('windowStart').addEventListener('change',()=>refreshWindow());
$('jumpAlarm').addEventListener('click',()=>{const alarm=annotatedAlarm();if(alarm===null)return;
 pauseReplay();const win=Number($('windowSeconds').value);replay.at=Math.max(0,Math.min(replayLimit(),alarm-win*.75));
 $('windowStart').value=String(replay.at);refreshWindow();showAlarmExplanation();});
$('windowSeconds').addEventListener('change',()=>{
 pauseReplay();const max=replayLimit();$('windowStart').max=String(max);
 replay.at=Math.min(Number($('windowStart').value),max);
 $('windowStart').value=String(replay.at);refreshWindow();
});$('refreshAudit').addEventListener('click',loadAudit);$('downloadReport').addEventListener('click',downloadReport);$('printReport').addEventListener('click',()=>{if(current)window.open('/api/records/'+encodeURIComponent(current.metadata.id)+'/report.html','_blank','noopener')});
$('faultSeverity').addEventListener('input',()=>text('severityValue',$('faultSeverity').value));window.addEventListener('resize',()=>{if(current)current.waveforms.forEach((w,i)=>{const canvases=document.querySelectorAll('.plot canvas');if(canvases[i])draw(canvases[i],w)})});
reloadRecords();

request('/api/wfdb/config').then(r=>text('wfdbRootInfo',r.configured?'Dataset folder: '+r.root:'Configure WAVEASSURE_WFDB_ROOT and restart the server')).catch(()=>{});

async function loadResearchModelStatus(){
  try {
    const status=await request('/api/research-model/status');
    researchModelAvailable=Boolean(status.available);
    text('modelState',researchModelAvailable?'Research model loaded':'Not trained');
    text('modelDetail',researchModelAvailable?'Locally trained retrospective model available. Results have no clinical use.':'No trained model is installed. Use scripts/train-vtac-windows.bat after enough valid labelled True and False events exist in official train/validation/test partitions.');
    $('assessBtn').disabled= !(researchModelAvailable && current && current.metadata.origin==='wfdb_research' && !current.metadata.parent_id && ['True','False'].includes(current.reference_label));
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
      wrap.append(info);const canvas=el('canvas');canvas.setAttribute('role','img');canvas.setAttribute('aria-label',(w.name||w.kind)+' pre-alarm waveform');wrap.append(canvas);$('pilotPlots').append(wrap);draw(canvas,w,{hideAlarm:true});
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
 if(pilotSession && pilotCase){const canvases=document.querySelectorAll('#pilotPlots .plot canvas');pilotWaveforms.forEach((w,i)=>{if(canvases[i])draw(canvases[i],w,{hideAlarm:true});});}
});

document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseReplay();});
