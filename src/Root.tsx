import React from 'react';
import {AbsoluteFill, Audio, Composition, Interactive, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import data from './empty-project.json';
import {nativeValue} from './nativeValues';
import type {Layer, Project} from './types';
import {DigitalPilot, type DigitalPilotProps} from './DigitalPilot';

const project = data as Project;
export const WordCaption: React.FC<{caption:Project['layout']['caption'];word:Project['captions'][number]}> = ({caption,word}) => {
  const frame=useCurrentFrame();
  const progress=interpolate(frame,[0,6],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const mode=caption.highlight??'underline';
  const scale=word.highlight && mode!=='glow' ? interpolate(frame,[0,6,11],[0.96,1.06,1],{extrapolateRight:'clamp'}) : 1;
  return <div style={{position:'absolute',left:caption.x,top:caption.y,width:caption.width,fontFamily:caption.fontFamily??'Arial',fontSize:caption.fontSize*(word.highlight && mode!=='glow'?1.16:1),fontWeight:caption.fontWeight??700,color:'white',textAlign:'center',WebkitTextStroke:`${caption.strokeWidth??1.5}px black`,paintOrder:'stroke fill',transform:`scale(${scale})`,isolation:'isolate'}}>
    <span style={{position:'relative',display:'inline-block',padding:word.highlight&&mode==='pill'?'2px 15px':undefined,borderRadius:12,background:word.highlight&&mode==='pill'?'#431624dc':undefined}}>{word.highlight&&mode==='glow'?<span style={{position:'absolute',inset:'4px -14px',background:'#fff',borderRadius:18,filter:'blur(18px)',opacity:0.95,zIndex:-1}}/>:null}{word.text}
      {word.highlight&&mode==='underline'?<span style={{position:'absolute',left:0,right:0,bottom:-5,height:4,background:caption.accentColor??'#b86b7a',transform:`scaleX(${progress})`,transformOrigin:'left'}}/>:null}
    </span>
  </div>;
};
export const Asset: React.FC<{layer:Layer;plainImage?:boolean}> = ({layer,plainImage}) => {
  const frame = useCurrentFrame();
  const Image = plainImage ? 'img' : Img;
  const {x, y, width, height} = layer.rect;
  const opacity = layer.transition === 'fade' && layer.fadeFrames > 0
    ? interpolate(frame, [0, layer.fadeFrames], [0, 1], {extrapolateRight:'clamp', extrapolateLeft:'clamp'}) : 1;
  const style: React.CSSProperties = {position:'absolute', left:x, top:y, width, height, opacity};
  if (layer.src && layer.crop) {
    const c=layer.crop;
    const scale=Math.min(width/c.width,height/c.height);
    return <div style={{...style,overflow:'hidden',clipPath:layer.clipPath,width:c.width*scale,height:c.height*scale,left:x+(width-c.width*scale)/2,top:y+(height-c.height*scale)/2}}><Image src={staticFile(layer.src)} style={{position:'absolute',maxWidth:'none',width:c.imageWidth*scale,height:c.imageHeight*scale,left:-c.x*scale,top:-c.y*scale}}/></div>;
  }
  if (layer.src) return <Image src={staticFile(layer.src)} style={{...style, objectFit:'contain'}}/>;
  return <div style={{...style, background:layer.color, border:'3px dashed #ffffff80', borderRadius:24, display:'flex', alignItems:'center', justifyContent:'center', textAlign:'center', padding:20, boxSizing:'border-box', color:'white', textShadow:'0 2px 5px black', fontSize:34}}>{layer.label}<br/>still pendente</div>;
};
export const NativeAsset: React.FC<{layer:Layer;sceneFrom:number}> = ({layer,sceneFrom}) => {
  const frame=useCurrentFrame(); const {fps}=useVideoConfig();
  const props=nativeValue(layer.native!.props,frame,fps);
  const zero={...layer,rect:{...layer.rect,x:0,y:0},native:undefined};
  return <Interactive.Div {...props} from={sceneFrom+layer.from} durationInFrames={layer.duration}><Asset layer={zero}/></Interactive.Div>;
};
export const FashionVideo: React.FC<Project & {lookContent?:React.ReactNode}> = (p) => {
  const caption = p.layout.caption;
  const frame = useCurrentFrame();
  const activeScene = p.scenes.find(s=>frame>=s.from && frame<s.from+s.duration);
  const overlaysVisible = !p.layout.revealOverlaysWithLooks || Boolean(activeScene && activeScene.layers.some(l=>frame>=activeScene.from+l.from));
  const base = p.layout.base;
  const baseTransform = base ? `translate(${base.x}px, ${base.y}px) scale(${base.scale})` : undefined;
  const grade=p.colorGrade;
  const baseFilter=grade ? `brightness(${grade.brightness??1}) contrast(${grade.contrast??1}) saturate(${grade.saturation??1}) sepia(${grade.warmth??0})` : undefined;
  const volume=Math.pow(10,(p.audioGainDb??0)/20);
  const pending = p.timingStatus !== 'reviewed' || Object.values(p.reviews).some(r=>r.status!=='passed') || p.scenes.some(s=>s.layers.some(l=>!l.src));
  return <AbsoluteFill style={{background:'#272b30', fontFamily:'Arial'}}>
    {p.audioSrc ? <Audio src={staticFile(p.audioSrc)} volume={volume} useWebAudioApi allowAmplificationDuringRender/> : null}
    {p.shots.length ? p.shots.map((shot,i)=><Sequence key={i} from={shot.from} durationInFrames={shot.outFrame-shot.inFrame}><OffthreadVideo src={staticFile(shot.src)} trimBefore={shot.inFrame} muted={Boolean(p.audioSrc)} volume={volume} useWebAudioApi allowAmplificationDuringRender style={{width:'100%',height:'100%',objectFit:'cover',filter:baseFilter,transform:baseTransform}}/></Sequence>) : p.source ? <OffthreadVideo src={staticFile(p.source)} muted={Boolean(p.audioSrc)} volume={volume} useWebAudioApi allowAmplificationDuringRender style={{width:'100%',height:'100%',objectFit:'cover',filter:baseFilter,transform:baseTransform}}/> : <AbsoluteFill style={{alignItems:'center',justifyContent:'flex-end',paddingBottom:530,color:'#abb2bb',fontSize:42}}>Aguardando corte do bruto</AbsoluteFill>}
    {(p.soundEffects??[]).map((cue,i)=><Sequence key={`sfx-${i}`} from={cue.from} durationInFrames={cue.duration}><Audio src={staticFile(cue.src)} volume={Math.pow(10,cue.gainDb/20)}/></Sequence>)}
    {p.lookContent ?? p.scenes.map(scene=>scene.layers.map(layer=>layer.native?<NativeAsset key={layer.id} layer={layer} sceneFrom={scene.from}/>:<Sequence key={layer.id} from={scene.from+layer.from} durationInFrames={layer.duration}><Asset layer={layer}/></Sequence>))}
    {overlaysVisible && p.layout.labels.map(label=>label.src ? <Asset key={label.text} layer={{id:label.text,src:label.src,label:label.text,color:'transparent',from:0,duration:1,transition:'cut',fadeFrames:0,rect:{x:label.x-(label.width??220)/2,y:label.y,width:label.width??220,height:label.height??140},crop:label.crop}}/> : label.bubble ? <svg key={label.text} width={320} height={145} style={{position:'absolute',left:label.x-160,top:label.y,overflow:'visible'}}><text x={160} y={82} textAnchor="middle" fontFamily={label.fontFamily??'Fredoka'} fontSize={100} fontWeight={700} fontStyle="italic" fill={label.color} stroke="white" strokeWidth={8} paintOrder="stroke fill" style={{filter:'drop-shadow(0 4px 1px #735f6f88) drop-shadow(0 7px 4px #0008)'}}>{label.text}</text></svg> : <div key={label.text} style={{position:'absolute',left:label.x,top:label.y,transform:'translateX(-50%)',fontFamily:label.fontFamily??'Arial',fontSize:label.fontSize??44,fontWeight:label.fontWeight??400,color:label.color??'white',WebkitTextStroke:`${label.strokeWidth??0}px black`,paintOrder:'stroke fill',textShadow:'0 2px 6px black'}}>{label.text}</div>)}
    {frame>0 && p.captions.map((c,i)=><Sequence key={i} from={c.from} durationInFrames={c.duration}><WordCaption caption={caption} word={c}/></Sequence>)}
    {p.previewGuides ? <AbsoluteFill style={{pointerEvents:'none'}}>
      <svg width={p.width} height={p.height} viewBox={`0 0 ${p.width} ${p.height}`} style={{position:'absolute',inset:0}}>
        <rect x={p.width*.06} y={p.height*.06} width={p.width*.88} height={p.height*.88} fill="none" stroke="#00e5ff" strokeWidth={3} strokeDasharray="14 9"/>
        <text x={p.width*.06+12} y={p.height*.06-12} fill="#00e5ff" stroke="#111" strokeWidth={2} paintOrder="stroke" fontSize={26}>SEGURANÇA · 6% EM CADA BORDA</text>
        {([['TOPO DA ROUPA',p.previewGuides.lookTop],['BARRA DA CALÇA',p.previewGuides.lookBottom]] as const).map(([label,y])=> y===undefined ? null : <g key={label}>
          <line x1={p.width*.06} x2={p.width*.94} y1={p.height*y} y2={p.height*y} stroke="#ffce54" strokeWidth={3} strokeDasharray="20 10"/>
          <text x={p.width/2} y={p.height*y-10} textAnchor="middle" fill="#ffce54" stroke="#111" strokeWidth={2} paintOrder="stroke" fontSize={26}>{label}</text>
        </g>)}
      </svg>
    </AbsoluteFill> : null}
    {pending ? <div style={{position:'absolute',bottom:50,width:'100%',textAlign:'center',fontSize:25,color:'white',textShadow:'0 1px 4px black'}}>{p.videoId} · PRÉVIA</div> : null}
  </AbsoluteFill>;
};
const ExportCheck: React.FC = () => {
  const frame=useCurrentFrame();
  return <AbsoluteFill style={{background:'#282b32',color:'white',fontFamily:'Arial',padding:100}}><h1 style={{fontSize:100}}>174 / TESTE TÉCNICO</h1><p style={{fontSize:54}}>1440 × 2560 · 60 fps</p><div style={{display:'flex',gap:30}}>{['#24354b','#172338','#652d3d'].map(c=><div key={c} style={{width:350,height:800,background:c}}/>)}</div><div style={{position:'absolute',top:1700,left:100+frame*15,width:140,height:140,background:'#f0e1a1'}}/><p style={{position:'absolute',bottom:200,fontSize:60}}>Quadro {frame} · sem material final</p></AbsoluteFill>;
};
const RawCheck: React.FC = () => <AbsoluteFill><OffthreadVideo src={staticFile('media/source-check.mov')} style={{width:'100%',height:'100%',objectFit:'cover'}}/><div style={{position:'absolute',top:180,left:80,color:'white',fontFamily:'Arial',fontSize:52,textShadow:'0 2px 8px black'}}>TESTE DE PIPELINE — NÃO É CORTE FINAL</div></AbsoluteFill>;
export const Root: React.FC = () => <>
  <Composition id="DigitalPilot" component={DigitalPilot} defaultProps={{width:1080,height:1920,fps:60,durationInFrames:60,source:'',audioSrc:'',groups:[],cards:[],zooms:[],soundEffects:[]} as DigitalPilotProps} width={1080} height={1920} fps={60} durationInFrames={60} calculateMetadata={({props})=>({width:props.width,height:props.height,fps:props.fps,durationInFrames:props.durationInFrames})}/>
  <Composition id="FashionVideo" component={FashionVideo} defaultProps={project} width={project.width} height={project.height} fps={project.fps} durationInFrames={project.durationInFrames} calculateMetadata={({props})=>({width:props.width,height:props.height,fps:props.fps,durationInFrames:props.durationInFrames})}/>
  <Composition id="RawCheck" component={RawCheck} width={1440} height={2560} fps={60} durationInFrames={60}/>
  <Composition id="ExportCheck" component={ExportCheck} width={1440} height={2560} fps={60} durationInFrames={60}/>
</>;
