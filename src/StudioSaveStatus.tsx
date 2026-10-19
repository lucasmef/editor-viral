import React, {useEffect, useState} from 'react';
import {staticFile} from 'remotion';
export const StudioSaveStatus: React.FC<{path:string}> = ({path}) => {
  const [state,setState]=useState({message:'Conectando salvamento…',ok:false,at:0});
  const [clock,setClock]=useState(Date.now());
  useEffect(()=>{let live=true;const poll=()=>{setClock(Date.now());fetch(staticFile(path)+'?t='+Date.now(),{cache:'no-store'}).then(r=>r.json()).then(s=>{if(live)setState(s);}).catch(()=>{if(live)setState({message:'Salvamento desconectado — não feche o Studio',ok:false,at:0});});};poll();const timer=setInterval(poll,1000);return()=>{live=false;clearInterval(timer);};},[path]);
  const stale=clock-state.at>6000;
  return <div style={{position:'absolute',bottom:4,left:0,width:'100%',textAlign:'center',fontFamily:'Arial',fontSize:24,padding:8,background:'#111e',color:!stale&&state.ok?'#8fffa7':'#ffcc66',pointerEvents:'none'}}>{stale?'Salvamento desconectado — não feche o Studio':state.message}</div>;
};
