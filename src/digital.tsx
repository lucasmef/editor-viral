import React from 'react';
import {AbsoluteFill, Composition, registerRoot, useCurrentFrame, spring, useVideoConfig} from 'remotion';
import {DigitalPilot, type DigitalPilotProps} from './DigitalPilot';

const defaults:DigitalPilotProps={width:1080,height:1920,fps:60,durationInFrames:60,source:'',audioSrc:'',groups:[],cards:[],zooms:[],soundEffects:[]};
const GraphicBridge:React.FC=()=>{
  const frame=useCurrentFrame();const {fps}=useVideoConfig();
  const entry=spring({frame,fps,config:{damping:24,stiffness:180}});
  return <AbsoluteFill style={{background:'#16251c',color:'#c4ff69',fontFamily:'Arial',justifyContent:'center',padding:90,boxSizing:'border-box'}}>
    <div style={{position:'absolute',width:900,height:900,border:'2px solid #c4ff6922',borderRadius:'50%',right:-430,top:-200,transform:`scale(${1+frame/700})`}}/>
    <div style={{fontSize:28,fontWeight:800,letterSpacing:6,marginBottom:42}}>ANTES DE LEVAR</div>
    <div style={{fontSize:119,fontWeight:900,lineHeight:.95,letterSpacing:-6,transform:`translateY(${(1-entry)*55}px)`,opacity:entry}}>TESTE<br/>POSSIBILI-<br/>DADES.</div>
    <div style={{height:10,background:'#c4ff69',width:frame*8+12,maxWidth:780,marginTop:48,borderRadius:9}}/>
    <div style={{fontSize:27,color:'#e3f0dd',letterSpacing:2,marginTop:38}}>JEANS · CALÇA · SAIA</div>
  </AbsoluteFill>;
};
registerRoot(()=> <>
  <Composition id="DigitalPilot" component={DigitalPilot} defaultProps={defaults} width={1080} height={1920} fps={60} durationInFrames={60} calculateMetadata={({props})=>({width:props.width,height:props.height,fps:props.fps,durationInFrames:props.durationInFrames})}/>
  <Composition id="DigitalBridge" component={GraphicBridge} width={1080} height={1920} fps={60} durationInFrames={77}/>
</>);
