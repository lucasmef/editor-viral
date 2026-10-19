"""Restore evicted dependency files from pnpm v11's local content store.

Decodes only the msgpackr record format used by this store. Verifies SHA-512
before replacing a dataless installed file; leaves online files unchanged.
"""
import argparse,hashlib,io,json,os,sqlite3,struct,tarfile,urllib.request
from pathlib import Path

class Unpack:
    def __init__(self,data):self.data=data;self.i=0;self.records={}
    def take(self,n):r=self.data[self.i:self.i+n];self.i+=n;return r
    def number(self,n):return int.from_bytes(self.take(n),'big')
    def read(self):
        b=self.number(1)
        if b in self.records:return {k:self.read() for k in self.records[b]}
        if b<128:return b
        if 0x80<=b<0x90:return {self.read():self.read() for _ in range(b-0x80)}
        if 0x90<=b<0xa0:return [self.read() for _ in range(b-0x90)]
        if 0xa0<=b<0xc0:return self.take(b-0xa0).decode()
        if b==0xc0:return None
        if b==0xc2:return False
        if b==0xc3:return True
        if b in (0xcc,0xcd,0xce,0xcf):return self.number(2**(b-0xcc))
        if b in (0xca,0xcb):return struct.unpack('>f' if b==0xca else '>d',self.take(4 if b==0xca else 8))[0]
        if b in (0xd9,0xda,0xdb):return self.take(self.number(2**(b-0xd9))).decode()
        if b in (0xdc,0xdd):return [self.read() for _ in range(self.number(2 if b==0xdc else 4))]
        if b in (0xde,0xdf):return {self.read():self.read() for _ in range(self.number(2 if b==0xde else 4))}
        if b==0xd4:
            typ=self.number(1);rid=self.number(1)
            if typ!=0x72:raise ValueError('Unknown extension')
            schema=self.read();self.records[rid]=schema
            return {k:self.read() for k in schema}
        raise ValueError('Unsupported msgpack byte '+hex(b))

p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--recover-missing',action='store_true');p.add_argument('--report',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];store=root/'.pnpm-store/v11'
con=sqlite3.connect('file:'+str(store/'index.db')+'?mode=ro',uri=True)
report={'applied':a.apply,'restored':[],'unavailable':[]}
for key,data in con.execute('select key,data from package_index'):
    pkg=Unpack(data).read();name=pkg['manifest']['name'];version=pkg['manifest']['version']
    prefix=name.replace('/','+')+'@'+version
    directories=[x/'node_modules'/name for x in (root/'node_modules/.pnpm').glob(prefix+'*') if x.name==prefix or x.name.startswith(prefix+'_')]
    directories=[x for x in directories if x.is_dir()]
    if not directories:continue
    archive=None
    for directory,rel,item in [(directory,rel,item) for directory in directories for rel,item in pkg['files'].items()]:
        dest=directory/rel
        if not dest.exists() or not (dest.stat().st_flags & 0x40000000):continue
        h=item['digest'];source=store/'files'/h[:2]/(h[2:]+('-exec' if item['mode'] & 0o111 else ''))
        if not source.is_file() or source.stat().st_flags & 0x40000000:
            if not a.recover_missing:
                report['unavailable'].append(str(dest));continue
            if archive is None:
                url='https://registry.npmjs.org/'+name+'/-/'+name.split('/')[-1]+'-'+version+'.tgz'
                print('Recovering exact package',name,version,flush=True)
                archive=tarfile.open(fileobj=io.BytesIO(urllib.request.urlopen(url,timeout=20).read()),mode='r:gz')
            content=archive.extractfile('package/'+rel).read()
        else:content=source.read_bytes()
        if hashlib.sha512(content).hexdigest()!=h or len(content)!=item['size']:raise ValueError('Integrity mismatch '+str(source))
        if a.apply:
            temp=dest.with_name(dest.name+'.verified-restore.tmp');temp.write_bytes(content);temp.chmod(item['mode']);os.replace(temp,dest)
        report['restored'].append({'path':str(dest),'sha512':h})
a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2))
print(json.dumps({'restored':len(report['restored']),'unavailable':len(report['unavailable']),'report':str(a.report)}))
