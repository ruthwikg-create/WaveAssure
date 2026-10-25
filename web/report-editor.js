/* Browser-only research report editor.
   Never posts, stores, serializes, or logs identifying information. */
(function(){
 'use strict';
 const ids=['studyLabel','studyId','age','sex','unit','recordedOn','reviewer','reviewerNotes'];
 const fields=ids.map(id=>document.getElementById(id));
 function update(){
   for(let i=0;i<ids.length;i++){
     const field=fields[i];
     const targets=document.querySelectorAll('[data-patient="'+ids[i]+'"]');
     let value=(field.value||'').trim();
     if(ids[i]==='age' && value && (!/^\d{1,3}$/.test(value)||Number(value)>120)){
       value='';
     }
     if(ids[i]==='recordedOn' && value && !/^\d{4}-\d{2}-\d{2}$/.test(value)){
       value='';
     }
     for(const target of targets)target.textContent=value||'Not provided';
   }
 }
 for(const field of fields){
   field.addEventListener('input',update);
   field.addEventListener('change',update);
 }
 document.getElementById('clearDetails').addEventListener('click',()=>{
   for(const field of fields)field.value='';
   update();
 });
 document.getElementById('printEvidence').addEventListener('click',()=>{
   update();
   window.print();
 });
 update();
})();
