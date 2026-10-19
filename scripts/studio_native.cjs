// Data-only import of editable native props. Never evaluates source code.
const {createRequire}=require('module');
const dep=createRequire(require.resolve('@remotion/cli'));
const parser=dep('@babel/parser'), generate=dep('@babel/generator').default;
const crypto=require('crypto'),fs=require('fs');
const calls=new Set(['useCurrentFrame','useVideoConfig','interpolate','interpolateColors','spring','Easing.linear','Easing.step1','Easing.bezier','Easing.spring','Easing.ease','Easing.quad','Easing.cubic','Easing.back','Easing.poly','Easing.in','Easing.out','Easing.inOut','Easing.sin','Easing.circle','Easing.exp','Easing.bounce','Easing.elastic','Math.min','Math.max','Math.abs','Math.round','Math.floor','Math.ceil']);
const name=n=>n.type==='Identifier'?n.name:n.type==='MemberExpression'&&!n.computed?name(n.object)+'.'+name(n.property):'';
function value(n){
 if(['StringLiteral','NumericLiteral','BooleanLiteral'].includes(n?.type))return n.value;
 if(n?.type==='NullLiteral')return null;
 if(n?.type==='Identifier'&&n.name==='undefined')return {$expr:'undefined'};
 if(n?.type==='Identifier'&&n.name==='frame')return {$expr:'frame'};
 if(n?.type==='Identifier'&&n.name==='fps')return {$expr:'fps'};
 if(n?.type==='MemberExpression'&&!n.computed&&n.property.name==='fps'&&n.object.type==='CallExpression'&&name(n.object.callee)==='useVideoConfig')return {$expr:'fps'};
 if(n?.type==='ArrayExpression')return n.elements.map(value);
 if(n?.type==='ObjectExpression')return Object.fromEntries(n.properties.map(p=>{if(p.type!=='ObjectProperty'||p.computed||['__proto__','constructor','prototype'].includes(p.key.name||p.key.value))throw Error('Objeto não suportado');return[p.key.name||p.key.value,value(p.value)];}));
 if(n?.type==='UnaryExpression'&&['-','+','!'].includes(n.operator))return {$expr:'unary',op:n.operator,arg:value(n.argument)};
 if(n?.type==='BinaryExpression'&&['+','-','*','/','%','**','<','>','<=','>=','===','!=='].includes(n.operator))return {$expr:'binary',op:n.operator,a:value(n.left),b:value(n.right)};
 if(n?.type==='ConditionalExpression')return {$expr:'conditional',test:value(n.test),yes:value(n.consequent),no:value(n.alternate)};
 if(n?.type==='TemplateLiteral')return {$expr:'template',parts:n.quasis.map(q=>q.value.cooked),values:n.expressions.map(value)};
 if(n?.type==='CallExpression'&&calls.has(name(n.callee)))return {$expr:'call',fn:name(n.callee),args:n.arguments.map(value)};
 if(n?.type==='MemberExpression'&&calls.has(name(n)))return {$expr:'function',fn:name(n)};
 throw Error('Expressão não suportada: '+generate(n).code);
}
const propNames=new Set(['name','from','durationInFrames','style','cropLeft','cropRight','cropTop','cropBottom','trimBefore','playbackRate','loop','freeze','hidden','showInTimeline','premountFor','postmountFor','styleWhilePremounted','styleWhilePostmounted']);
function hash(n){n=JSON.parse(JSON.stringify(n,(k,v)=>['extra','loc','start','end','comments','leadingComments','trailingComments','innerComments'].includes(k)?undefined:v));return crypto.createHash('sha256').update(generate(n,{comments:false,compact:true}).code).digest('hex');}
function parseNative(source){
 const ast=parser.parse(source,{sourceType:'module',plugins:['typescript','jsx']});const layers=[];
 const looks=ast.program.body.flatMap(n=>n.type==='VariableDeclaration'?n.declarations:[]).find(n=>n.id.name==='Looks');
 if(!looks)throw Error('Componente de looks ausente');
 let body=looks.init.body;
 if(body.type==='BlockStatement')body=body.body.find(n=>n.type==='ReturnStatement')?.argument;
 function checkTree(n){
  if(n?.type==='JSXFragment'){n.children.forEach(c=>{if(c.type==='JSXText'&&!c.value.trim())return;checkTree(c);});return;}
  if(n?.type==='JSXElement'&&n.openingElement.name.type==='JSXMemberExpression'&&n.openingElement.name.object.name==='Interactive'&&n.openingElement.name.property.name==='Div')return;
  throw Error('Esta ação muda a estrutura da composição (efeitos/pre-compose/novos elementos). Desfaça; os ajustes de peças anteriores estão preservados.');
 }
 checkTree(body);

 function walk(n){if(!n||typeof n!=='object')return;
 if(n.type==='JSXElement'&&n.openingElement.name.type==='JSXMemberExpression'&&n.openingElement.name.object.name==='Interactive'&&n.openingElement.name.property.name==='Div'){
  let id,props={};for(const a of n.openingElement.attributes){if(a.type!=='JSXAttribute')throw Error('Spread não permitido');const k=a.name.name;if(k==='data-piece'){id=a.value.value;continue;}if(!propNames.has(k))throw Error('Propriedade não suportada: '+k);props[k]=a.value===null?true:value(a.value.type==='JSXExpressionContainer'?a.value.expression:a.value);}
  if(!id)throw Error('Peça sem identidade');const children=n.children.filter(c=>c.type!=='JSXText'||c.value.trim());
  if(children.length!==1||children[0].type!=='JSXElement'||children[0].openingElement.name.name!=='Asset')throw Error('Conteúdo da peça alterado');
  layers.push({id,props,assetSignature:hash(children[0])});return;
 }
 for(const [k,v] of Object.entries(n))if(!['loc','start','end','extra'].includes(k)){if(Array.isArray(v))v.forEach(walk);else if(v&&typeof v==='object')walk(v);}}
 walk(ast);return {layers};
}
module.exports={parse:parseNative};
if(require.main===module){try{process.stdout.write(JSON.stringify(parseNative(fs.readFileSync(process.argv[2],'utf8'))));}catch(e){console.error(e.message);process.exit(1);}}
