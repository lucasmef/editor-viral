// This local editing session must never listen on a network interface.
const net=require('node:net');
const listen=net.Server.prototype.listen;
net.Server.prototype.listen=function(options,...rest){
 if(options && typeof options==='object' && 'port' in options)options={...options,host:'127.0.0.1'};
 return listen.call(this,options,...rest);
};
