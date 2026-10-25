/* Pure retrospective replay geometry. No clinical detection or sample changes. */
(function(root){
 'use strict';
 const bounded=(v,lo,hi)=>Math.max(lo,Math.min(hi,Number(v)||0));
 function startFor(playhead,windowSeconds,duration){
   const d=Math.max(0,Number(duration)||0),w=Math.max(0,Number(windowSeconds)||0);
   return bounded(playhead-w/2,0,Math.max(0,d-w));
 }
 function advance(playhead,deltaSeconds,speed,duration){
   const d=Math.max(0,Number(duration)||0);
   return bounded((Number(playhead)||0)+Math.max(0,Number(deltaSeconds)||0)*Math.max(0,Number(speed)||0),0,d);
 }
 function crossedEvent(before,after,eventSeconds){
   return Number.isFinite(eventSeconds)&&eventSeconds>=0&&before<eventSeconds&&after>=eventSeconds;
 }
 function cursorX(waveform,playhead,width,left=13,right=10){
   if(!waveform||!Array.isArray(waveform.t)||waveform.t.length<2)return null;
   const min=Number(waveform.t[0]),max=Number(waveform.t[waveform.t.length-1]);
   if(!Number.isFinite(min)||!Number.isFinite(max)||max<=min||playhead<min||playhead>max)return null;
   return left+(playhead-min)/(max-min)*Math.max(0,width-left-right);
 }
 root.WaveAssureReplay=Object.freeze({startFor,advance,crossedEvent,cursorX});
})(typeof window==='undefined'?globalThis:window);
