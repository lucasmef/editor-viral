import {Easing, interpolate, interpolateColors, spring} from 'remotion';
// Restricted data expressions emitted by Studio, not arbitrary JavaScript/eval.
export function nativeValue(v:any,frame:number,fps:number):any {
 if(v===null||typeof v!=='object')return v;
 if(Array.isArray(v))return v.map(x=>nativeValue(x,frame,fps));
 const ev=(x:any)=>nativeValue(x,frame,fps);
 const functions:Record<string,any>={interpolate,interpolateColors,spring,useCurrentFrame:()=>frame,useVideoConfig:()=>({fps}),...Object.fromEntries(Object.entries(Easing).map(([k,x])=>['Easing.'+k,x])),...Object.fromEntries(['min','max','abs','round','floor','ceil'].map(k=>['Math.'+k,(Math as any)[k]]))};
 if(v.$expr){switch(v.$expr){
 case 'undefined':return undefined;
 case 'frame':return frame;
 case 'fps':return fps;
 case 'function':if(!functions[v.fn])throw Error('Função inválida');return functions[v.fn];
 case 'call':if(!functions[v.fn])throw Error('Função inválida');return functions[v.fn](...v.args.map(ev));
 case 'template':return v.parts.map((s:string,i:number)=>s+(i<v.values.length?ev(v.values[i]):'')).join('');
 case 'conditional':return ev(v.test)?ev(v.yes):ev(v.no);
 case 'unary':return v.op==='-'?-ev(v.arg):v.op==='+'?+ev(v.arg):!ev(v.arg);
 case 'binary':{const a=ev(v.a),b=ev(v.b);switch(v.op){case '+':return a+b;case '-':return a-b;case '*':return a*b;case '/':return a/b;case '%':return a%b;case '**':return a**b;case '<':return a<b;case '>':return a>b;case '<=':return a<=b;case '>=':return a>=b;case '===':return a===b;case '!==':return a!==b;}throw Error('Operador inválido');}
 default:throw Error('Expressão inválida');}}
 return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,ev(x)]));
}
