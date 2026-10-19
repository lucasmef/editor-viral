import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {safeMoveScript} from './safe-move-script.js';
const TPS=254016000000, frame=TPS/60;
function fixture({stage=true,blocked=false,linked=false,animated=false,damage=false,sourceNeighbour=true,targetOld=true,locked=false,transition=false}={}) {
 const clip=(id,s,e)=>({nodeId:id,name:id,start:{ticks:String(s*TPS)},end:{ticks:String(e*TPS)},inPoint:{ticks:'0'},outPoint:{ticks:String((e-s)*TPS)},disabled:false,projectItem:{nodeId:'media-'+id},getSpeed:()=>1,isSpeedReversed:()=>false,getLinkedItems:()=>({numItems:0}),components:{numItems:1,0:{matchName:'Motion',displayName:'Motion',properties:{numItems:1,0:{displayName:'Scale',getValue:()=>93,isTimeVarying:()=>false}}}}});
 const moving=clip('copy',0,2), original=clip('original',0,2), neighbour=clip('neighbour',4,6);
 if(linked)moving.getLinkedItems=()=>({numItems:1,0:{nodeId:'partner'}});
 if(animated)moving.components[0].properties[0].isTimeVarying=()=>true;
 const track=items=>({clips:Object.defineProperty(items,'numItems',{get(){return this.length}}),isLocked:()=>false,transitions:{numItems:0}});
 const ts=[track([...(targetOld?[original]:[]),...(blocked?[clip('blocker',4,6)]:[])]),track([moving,...(sourceNeighbour?[neighbour]:[])]),...(stage?[track([])]:[])];ts.numTracks=ts.length;if(locked)ts[0].isLocked=()=>true;if(transition)ts[0].transitions.numItems=1;
 const seq={timebase:String(frame),videoTracks:ts,audioTracks:{numTracks:0}};
 const find=id=>{for(let i=0;i<ts.length;i++){const c=ts[i].clips.find(c=>c.nodeId===id);if(c)return{clip:c,trackIndex:i,trackType:'video'}}};
 let writes=0;
 const ctx={__findClip:find,__secondsToTicks:s=>s*TPS,__snapSequenceTicks:(_,t)=>Math.round(t/frame)*frame,__ticksToSeconds:t=>Number(t)/TPS,__jsonStringify:JSON.stringify,__result:data=>({ok:true,data}),__error:(error,data)=>({ok:false,error,data}),__writeClipSpan:(c,s,e)=>{writes++;c.start.ticks=String(s);c.end.ticks=String(e)},app:{project:{activeSequence:seq},enableQE(){}},qe:{project:{getActiveSequence:()=>({getVideoTrackAt:i=>({numItems:ts[i].clips.length,getItemAt:q=>{const c=ts[i].clips[q];return{type:'Clip',start:c.start,moveToTrack(delta){writes++;const to=ts[i+delta].clips;for(let j=to.length-1;j>=0;j--)if(+to[j].start.ticks<+c.end.ticks&&+to[j].end.ticks>+c.start.ticks)to.splice(j,1);ts[i].clips.splice(ts[i].clips.indexOf(c),1);to.push(c);if(damage)original.name='corrupted'}}}})})}}};
 return{run:()=>vm.runInNewContext('(function(){'+safeMoveScript('copy',4,0)+'})()',ctx),find,writes:()=>writes};
}
test('regression: occupied old destination and source final time use free staging track',()=>{const f=fixture();const r=f.run();assert.equal(r.ok,true);assert.equal(r.data.route,'via_free_track');assert.equal(f.find('original').clip.name,'original');assert.equal(f.find('neighbour').trackIndex,1);assert.equal(f.find('copy').trackIndex,0);assert.equal(f.find('copy').clip.components[0].properties[0].getValue(),93)});
for(const [name,opts] of [['occupied final destination',{blocked:true}],['no safe route',{stage:false}],['linked clip',{linked:true}],['animated clip',{animated:true}]])test(name+' refuses before writes',()=>{const f=fixture(opts);assert.equal(f.run().ok,false);assert.equal(f.writes(),0)});
test('collateral change cannot be reported as verified',()=>{const f=fixture({damage:true});const r=f.run();assert.equal(r.ok,false);assert.equal(r.data.verified,false);assert.equal(r.data.outcome,'committed_unverified');assert.match(r.error,/preservation mismatch/)});

for (const [name,options,route] of [['source path clear',{sourceNeighbour:false},'time_then_track'],['destination path clear',{targetOld:false},'track_then_time']]) test(name,()=>{const f=fixture(options);const r=f.run();assert.equal(r.ok,true,JSON.stringify(r));assert.equal(r.data.route,route);assert.equal(f.find('copy').trackIndex,0)});
for(const options of [{locked:true},{transition:true}])test('locked or transitioned destination rejected',()=>{const f=fixture(options);assert.equal(f.run().ok,false);assert.equal(f.writes(),0)});
