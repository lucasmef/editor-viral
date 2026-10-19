import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export type TimedWord = {text:string;from:number;duration:number};
export type CaptionGroup = {from:number;duration:number;words:TimedWord[]};
export type MotionCard = {from:number;duration:number;kicker:string;text:string;items?:{text:string;from:number}[];tone?:'mint'|'orange'};
export type DigitalPilotProps = {
  width:number;height:number;fps:number;durationInFrames:number;source:string;audioSrc:string;
  groups:CaptionGroup[];cards:MotionCard[];
  zooms:{from:number;to:number;scale:number;y:number}[];
  soundEffects:{src:string;from:number;duration:number;gainDb:number}[];
};

const colors={mint:'#c4ff69',orange:'#ffb58f',ink:'#121916'};
const ease=(x:number)=>x*x*(3-2*x);

const CaptionBlock:React.FC<{group:CaptionGroup}> = ({group})=>{
  const frame=useCurrentFrame();const {fps}=useVideoConfig();
  const entrance=spring({frame,fps,config:{damping:25,stiffness:280},durationInFrames:12});
  return <div style={{position:'absolute',left:82,right:82,bottom:212,textAlign:'center',transform:`translateY(${(1-entrance)*14}px)`,opacity:interpolate(frame,[0,3],[0,1],{extrapolateRight:'clamp'}),fontFamily:'Arial',fontWeight:800,fontSize:64,lineHeight:1.25,letterSpacing:-1.6}}>
    <div style={{display:'inline',boxDecorationBreak:'clone',padding:'13px 22px',borderRadius:20,background:'rgba(12,19,17,.89)',boxShadow:'0 10px 36px #0003'}}>
      {group.words.map((w,i)=>{
        const active=frame>=w.from-group.from&&frame<w.from-group.from+w.duration;
        return <React.Fragment key={i}><span style={{color:active?colors.mint:'#fff',textShadow:'0 2px 3px #0008'}}>{w.text}</span>{i<group.words.length-1?' ':''}</React.Fragment>;
      })}
    </div>
  </div>;
};

const Card:React.FC<{card:MotionCard}> = ({card})=>{
  const frame=useCurrentFrame();const {fps}=useVideoConfig();
  const entry=spring({frame,fps,config:{damping:22,stiffness:180},durationInFrames:22});
  const opacity=interpolate(frame,[0,5,card.duration-8,card.duration],[0,1,1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const accent=colors[card.tone??'mint'];
  return <div style={{position:'absolute',top:155,left:80,right:80,color:'#fff',opacity,transform:`translateY(${(1-entry)*-26}px) scale(${.97+.03*entry})`,transformOrigin:'center top',fontFamily:'Arial'}}>
    <div style={{display:'inline-block',fontSize:24,fontWeight:800,letterSpacing:4,color:accent,background:colors.ink,padding:'10px 18px',borderRadius:7}}>{card.kicker}</div>
    <div style={{fontSize:78,fontWeight:900,letterSpacing:-3,lineHeight:1.02,marginTop:16,maxWidth:900,textShadow:'0 3px 26px #000b'}}>{card.text}</div>
    <div style={{height:7,background:accent,width:interpolate(frame,[4,26],[0,150],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}),borderRadius:6,marginTop:20}}/>
    {card.items&&<div style={{display:'flex',gap:12,flexWrap:'wrap',marginTop:24}}>{card.items.map((item,i)=>{
      const f=frame-item.from;if(f<0)return null;
      const reveal=spring({frame:f,fps,config:{damping:18,stiffness:220}});
      return <div key={i} style={{fontSize:27,fontWeight:800,padding:'14px 20px',borderRadius:12,background:accent,color:colors.ink,opacity:reveal,transform:`translateY(${(1-reveal)*14}px)`}}>{item.text}</div>;
    })}</div>}
  </div>;
};

export const DigitalPilot:React.FC<DigitalPilotProps> = p=>{
  const frame=useCurrentFrame();
  const z=p.zooms.find(x=>frame>=x.from&&frame<x.to);
  const entry=z?ease(Math.min(1,Math.max(0,(frame-z.from)/22))):0;
  const scale=z?1.08+(z.scale-1.08)*entry:1.08;
  const y=z?-62+(z.y+62)*entry:-62;
  return <AbsoluteFill style={{background:'#121916'}}>
    <OffthreadVideo src={staticFile(p.source)} muted style={{width:'100%',height:'100%',objectFit:'cover',transform:`translateY(${y}px) scale(${scale})`,filter:'contrast(1.035) saturate(1.04)'}}/>
    <Audio src={staticFile(p.audioSrc)}/>
    {p.soundEffects.map((cue,i)=><Sequence key={i} from={cue.from} durationInFrames={cue.duration}><Audio src={staticFile(cue.src)} volume={Math.pow(10,cue.gainDb/20)}/></Sequence>)}
    <AbsoluteFill style={{background:'linear-gradient(180deg,rgba(0,0,0,.20),transparent 32%,transparent 75%,rgba(0,0,0,.16))',pointerEvents:'none'}}/>
    {p.cards.map((card,i)=><Sequence key={i} from={card.from} durationInFrames={card.duration}><Card card={card}/></Sequence>)}
    {p.groups.map((group,i)=><Sequence key={i} from={group.from} durationInFrames={group.duration}><CaptionBlock group={group}/></Sequence>)}
  </AbsoluteFill>;
};
