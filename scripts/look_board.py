#!/usr/bin/env python3
"""Render a non-generative look review from an explicit JSON recipe (Pillow)."""
import argparse, base64, hashlib, html, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def render(recipe_path, out):
    data=json.loads(Path(recipe_path).read_text());out=Path(out);out.mkdir(parents=True,exist_ok=True)
    pieces={}
    for p in data['pieces']:
        src=Path(p['source']);assert hashlib.sha256(src.read_bytes()).hexdigest()==p['sha256'],src
        im=Image.open(src).convert('RGBA')
        box=p['crop']
        im=im.crop(tuple(round(v*(im.width if i%2==0 else im.height)) for i,v in enumerate(box)))
        pieces[p['id']]=im
    boards=[];cards=[]
    fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
    font=ImageFont.truetype(fontpath,22);small=ImageFont.truetype(fontpath,17)
    for b in data['boards']:
        canvas=Image.new('RGB',(600,960),'#f5f3ed');draw=ImageDraw.Draw(canvas)
        draw.text((24,20),b['title'],font=font,fill='#252923')
        draw.text((24,54),'COLAGEM DE VALIDAÇÃO • SEM IA',font=small,fill='#68705e')
        for layer in b['layers']:
            im=pieces[layer['piece']].copy()
            im.thumbnail((layer.get('width',400),layer.get('height',350)),Image.Resampling.LANCZOS)
            canvas.paste(im,(round(layer['x']-im.width/2),layer['y']))
        for i,line in enumerate(b['footer']):draw.text((24,855+i*27),line,font=small,fill='#624f3c')
        file=out/(b['id']+'.jpg');canvas.save(file,quality=93);boards.append(canvas)
        uri='data:image/jpeg;base64,'+base64.b64encode(file.read_bytes()).decode()
        cards.append('<article><img src="'+uri+'" alt="'+html.escape(b['title'])+'"><p>'+html.escape(b['description'])+'</p></article>')
    sheet=Image.new('RGB',(600*len(boards),960),'white')
    for i,b in enumerate(boards):sheet.paste(b,(600*i,0))
    sheet.save(out/'looks-177.jpg',quality=92)
    sources=''
    for p in data['pieces']:
        im=pieces[p['id']];preview=Image.new('RGB',im.size,'#f5f3ed');preview.paste(im,mask=im.getchannel('A'))
        import io
        buf=io.BytesIO();preview.save(buf,format='PNG');uri='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
        sources+='<div><img src="'+uri+'"><p>'+html.escape(p['label'])+'</p><a href="'+html.escape(p['url'],quote=True)+'">Produto na marca ↗</a></div>'
    page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>177 — Validação dos looks</title><style>body{font:16px/1.5 system-ui;background:#f5f3ed;color:#252923;margin:30px}h1{font-size:36px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}article{background:white;padding:12px;border-radius:14px}article img{width:100%}aside{margin:24px 0;padding:20px;background:#efe4cd}.sources{display:flex;flex-wrap:wrap;gap:20px}.sources div{width:160px}.sources img{width:160px;height:200px;object-fit:contain}a{color:#345634}</style><h1>177 · Looks para validar</h1><p>Uma foto por produto. Fotos em retângulos: parte de cima acima, calça ou saia abaixo; não são stills finais. Sem máscaras, remoção de fundo ou encaixe de silhuetas. Não há aprovação registrada.</p><main>'''+''.join(cards)+'''</main><aside><b>Complementos de luxo — etapa posterior</b><p>Cena 1: burgundy. Cena 2: camel. Cena 3: vermelho. Cena 4: azul-claro. Fora da coleta atual de roupas-base. Calçados e acessórios não foram selecionados. O masculino será pesquisado em separado.</p></aside><h2>Uma referência por peça</h2><div class="sources">'''+sources+'''</div><p>Roteiro: brief.json do vídeo 177. Peças e vínculos atualizados conforme os links e instruções de Lucas. Esta prévia não constitui aprovação do resultado final. As demais fotos antigas foram preservadas fora desta apresentação.</p></html>'''
    (out/'index.html').write_text(page)
    print(out/'index.html')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('recipe');ap.add_argument('out');a=ap.parse_args();render(a.recipe,a.out)
