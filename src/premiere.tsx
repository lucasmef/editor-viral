// Interchange-only rasterization. Does not register in the working Studio.
import React from 'react';
import {AbsoluteFill, Composition, registerRoot, useCurrentFrame} from 'remotion';
import {Asset, NativeAsset, WordCaption} from './Root';
const Pieces: React.FC<any> = ({project:p,items}) => {
 const i=items[useCurrentFrame()];
 if(i.kind==='piece') {const layer={...i.layer,from:0,duration:items.length,transition:'cut',fadeFrames:0};return <AbsoluteFill>{layer.native?<NativeAsset layer={layer} sceneFrom={0}/>:<Asset layer={layer}/>}</AbsoluteFill>;}
 if(i.kind==='caption')return <AbsoluteFill style={{fontFamily:'Arial'}}><WordCaption caption={p.layout.caption} word={i.word}/></AbsoluteFill>;
 const g=p.previewGuides;
 return <svg width={p.width} height={p.height}><rect x={p.width*.06} y={p.height*.06} width={p.width*.88} height={p.height*.88} fill="none" stroke="#00e5ff" strokeWidth={3} strokeDasharray="14 9"/>{[g.lookTop,g.lookBottom].filter(y=>y!==undefined).map((y,j)=><g key={j}><line x1={p.width*.06} x2={p.width*.94} y1={p.height*y} y2={p.height*y} stroke="#ffce54" strokeWidth={3} strokeDasharray="20 10"/><text x={p.width/2} y={p.height*y-10} textAnchor="middle" fill="#ffce54" stroke="#111" strokeWidth={2} paintOrder="stroke" fontSize={26}>{j?'BARRA DA CALÇA':'TOPO DA ROUPA'}</text></g>)}</svg>;
};
registerRoot(()=> <Composition id="PremierePieces" component={Pieces} width={1440} height={2560} fps={60} durationInFrames={1} defaultProps={{project:{},items:[]}} calculateMetadata={({props}:any)=>({width:props.project.width,height:props.project.height,fps:props.project.fps,durationInFrames:props.items.length})}/>);
