// Parse native Studio edits as data, without evaluating TSX.
const {createRequire}=require('module');
const dependency=createRequire(require.resolve('@remotion/cli'));
const parser=dependency('@babel/parser');
const generate=dependency('@babel/generator').default;
const fs=require('fs'), crypto=require('crypto');
function parse(source) {
 const ast=parser.parse(source,{sourceType:'module',plugins:['typescript','jsx']});
 const layers=[];
 function visit(n) {
  if(!n || typeof n!=='object')return;
  if(n.type==='JSXOpeningElement' && n.name.type==='JSXMemberExpression' && n.name.object.name==='Interactive' && n.name.property.name==='Div') {
   const attrs=Object.fromEntries(n.attributes.map(a=>[a.name?.name,a.value]));
   const id=attrs['data-piece']?.value, style=attrs.style?.expression;
   if(!id || style?.type!=='ObjectExpression')throw Error('Peça sem identidade/estilo');
   const props=Object.fromEntries(style.properties.map(p=>[p.key?.name,p]));
   const tr=props.translate?.value,sc=props.scale?.value;
   if(tr?.type!=='StringLiteral'||!sc)throw Error('Posição e escala devem ser estáticas');
   const match=tr.value.match(/^(-?\d+(?:\.\d+)?)px\s+(-?\d+(?:\.\d+)?)px$/);
   const scale=['NumericLiteral','StringLiteral'].includes(sc.type)?Number(sc.value):NaN;
   if(!match||!Number.isFinite(scale)||scale<=0||scale>10)throw Error('Use posição e escala proporcional positivas, sem animação');
   layers.push({id,x:Number(match[1]),y:Number(match[2]),scale});
   props.translate.value={type:'NumericLiteral',value:0};props.scale.value={type:'NumericLiteral',value:0};
  }
  for(const [k,v] of Object.entries(n))if(!['loc','start','end','extra'].includes(k)) {if(Array.isArray(v))v.forEach(visit);else if(v&&typeof v==='object')visit(v);}
 }
 visit(ast);
 if(new Set(layers.map(l=>l.id)).size!==layers.length)throw Error('Peça duplicada');
 return {layers,signature:crypto.createHash('sha256').update(generate(ast,{comments:false,compact:true}).code).digest('hex')};
}
module.exports={parse};
if(require.main===module){try{process.stdout.write(JSON.stringify(parse(fs.readFileSync(process.argv[2],'utf8'))));}catch(e){console.error(e.message);process.exit(1);}}
