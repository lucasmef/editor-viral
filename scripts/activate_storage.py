"""Activate empty external 174 after verified, non-destructive relocation."""
import studio as s

r=s.paths();journal=r['edit']/'_editor/migrations/20261013-relocation-v3.json'
assert s.read(journal)['state']=='completed','Relocação não terminou'
archive=r['edit']/'_editor/research/migration-20261013'
assert not s.catalog_path().exists(),'Catálogo já ativado'
old=s.read(archive/'retired-library/media.json')
originals={mid:item for mid,item in old['media'].items() if item['kind']=='original'}
for mid,item in originals.items():
    assert any(s.sha(p)==item['sha256'] for p in item['locations']),'Original não corresponde'
s.write(s.catalog_path(),{'schemaVersion':1,'media':originals},True)
s.init_job('174','Recomeçar do zero, conforme Lucas. Referência de linguagem: vídeo 101, girl à esquerda e boy à direita. Nenhum corte, look, aprovação ou acabamento herdado.')
s.log('174','fresh-start',reason='Reinício explícito solicitado por Lucas durante migração de armazenamento')
s.overview('174')
s.write(r['edit']/'_editor/migrations/20261013-activation.json',{'originalsVerified':list(originals),'job174':str(s.jobdir('174')),'scenes':0,'approvalInherited':False,'rawDeleted':False},True)
print(s.jobdir('174'))
