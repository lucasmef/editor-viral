# Cabelo: MatAnyone 2 e controles de recomposição

> Formato de acabamento definido por Lucas: tomadas com margens em 2160 × 3840, 60 fps, ProRes 422 Standard (perfil 2), nunca HQ ou LT. A entrega 1440 × 2560 é independente. Reextrair do bruto 4K; não ampliar acabamento menor. Contrato e limitações atuais em [acabamento com margens](../skills/raquel-video-editor/references/finishing-handles.md).
> Direção atual de Lucas (14/10/2026): nos próximos processamentos, preservar preferencialmente 1 s real antes e depois de cada cena/tomada (0,5 s quando a janela útil for menor), para ajustes posteriores do corte e mudanças de ordem. Registrar as margens disponíveis e rever as junções após reordenar; a reserva não é uma pausa obrigatória na montagem. Ver [contrato de margens](../skills/raquel-video-editor/references/finishing-handles.md). Os comandos legados abaixo vinculam a saída ao corte completo. Para maquiagem/cabelo usar a receita 4K com `--window-work` e `window-publish`, descrita no contrato. Janelas de voz ainda exigem adaptação. Não prometer reaproveitamento automático nem alterar hashes para contornar essa limitação.

> Migração de armazenamento: raízes em `studio/storage.json`. Projetos atuais ficam em `Edit/<id>/project`; saídas de voz em `Edit/<id>/audio`, rosto em `face` e cabelo em `hair`. `face-base`, `hair-prepare` e `hair-render` podem escolher um novo diretório em Edit quando --work for omitido. As etapas seguintes recebem esse mesmo caminho. O 174 foi reiniciado: exemplos antigos e evidências em `analysis/` abaixo são históricos, agora sob `/Users/lucas/Movies/Vídeos/Edit/_editor/research/migration-20261013/analysis/`; não são configuração ativa nem promessa de execução desses experimentos antigos.

Etapa local **deste editor**, independente do Rosto Natural. Interfaces: `scripts/hair_analyze.py` (análise) e `scripts/hair_finish.py` (cache, configuração e recomposição). Implementação dos controles: `scripts/hair_controls.py`, versão `hair-controls-v1`. Integração com jobs: `scripts/hair_connector.py`, contrato `editor-hair-v1`, acessível por `studio.py hair-*`.

O agente desenha/revisa a máscara inicial de cada cena; o MatAnyone 2 a propaga. A máscara original fica preservada. Níveis, expansão/contração, feather e composição são derivados posteriores, sem classificar cabelo pela luminosidade e sem nova inferência a cada ajuste.

## Ambiente e comandos

Ambiente disponível neste workspace, sem nova instalação:

```sh
HAIR_PY=.runtime/hair/venv/bin/python
"$HAIR_PY" scripts/hair_finish.py --help
"$HAIR_PY" scripts/hair_analyze.py --help
```

`hair_finish` precisa de Python, NumPy, OpenCV e FFmpeg/ffprobe. `hair_analyze` também precisa de Torch, Hydra, OmegaConf e do código/pesos locais do MatAnyone 2. Dependências congeladas em `.runtime/hair/requirements.lock.txt`. Não usa a rede nem baixa modelos. `FFMPEG`/`FFPROBE` podem indicar binários; por padrão utiliza os disponíveis pelo harness.

MPS deve estar visível ao processo de análise. CPU só quando escolhido explicitamente no plano. Recomposição dos controles não precisa do modelo nem da GPU MPS. O ambiente `.venv` principal não tem OpenCV nesta instalação; use o ambiente acima, inclusive nos testes numéricos.

## Ajustar o cache do 174 já aprovado como amostra

Cache preparado e conferido: `analysis/hair-validation/controls-v12/cache-final/cache.json`. Ele referencia os alphas originais v11 e proxies lossless, sem sobrescrevê-los. Os dados específicos do 174 estão em `analysis/`, não embutidos no módulo reutilizável.

```sh
# Cada arquivo/diretório de saída deve ser novo.
"$HAIR_PY" scripts/hair_finish.py init \
  --cache analysis/hair-validation/controls-v12/cache-final/cache.json \
  --out analysis/hair-validation/174-hair-settings-v02.json

# Editar o JSON gerado; conferir antes de renderizar.
"$HAIR_PY" scripts/hair_finish.py validate \
  --cache analysis/hair-validation/controls-v12/cache-final/cache.json \
  --config analysis/hair-validation/174-hair-settings-v02.json \
  --project jobs/174/project.json

# Teste curto: quadros locais [0,120) da cena, sem mudança de velocidade.
"$HAIR_PY" scripts/hair_finish.py render \
  --cache analysis/hair-validation/controls-v12/cache-final/cache.json \
  --config analysis/hair-validation/174-hair-settings-v02.json \
  --project jobs/174/project.json --scene 174-1 --frames 0:120 \
  --save-masks --out analysis/hair-validation/174-hair-test-v02

# Corte completo: omitir --scene e --frames.
"$HAIR_PY" scripts/hair_finish.py render \
  --cache analysis/hair-validation/controls-v12/cache-final/cache.json \
  --config analysis/hair-validation/174-hair-settings-v02.json \
  --project jobs/174/project.json \
  --out analysis/hair-validation/174-hair-full-v02
```

Não alterar `cacheId` para reaproveitar uma configuração em outro vídeo: gerar com `init` e transferir apenas os ajustes revisados.

## Configuração e unidades

`defaults` se aplica a todas as cenas. `scenes.<id>` substitui apenas os campos informados. Os IDs são os IDs reais do projeto. Chaves desconhecidas, valores não finitos, cache errado e intervalos inválidos são recusados.

| Controle | Padrão | Efeito e unidade |
|---|---:|---|
| `alpha.black` | 0 | Alpha abaixo deste nível vira transparente; intervalo 0..1 |
| `alpha.white` | 1 | Alpha acima deste nível vira opaco; deve ser maior que black |
| `alpha.gamma` | 1 | `alpha^(1/gamma)`: maior que 1 aumenta opacidade intermediária |
| `alpha.offsetPx` | 0 | Positivo expande, negativo contrai; raio de morfologia em pixels do alpha, inclusive frações |
| `alpha.featherPx` | 0,6 | Sigma da suavização, em pixels do alpha; zero desliga |
| `alpha.featherMode` | `outward` | Suavização externa, sem diminuir o alpha que chega a essa etapa; `symmetric` permite transição nos dois lados |
| `alpha.protectOpaque` | `true` | Repõe alpha 1 em todo pixel originalmente opaco, mesmo depois de níveis/contração/feather |
| `intensity` | 1 | Intensidade da substituição do fundo, 0..1; zero é bypass exato antes da codificação |
| `background.donorOffsetNative` | do cache | `[dx,dy]` do vídeo doador em pixels da fonte nativa; positivo desloca o doador para direita/baixo |
| `background.gainRgb` | `[1,1,1]` | Multiplicador fixo da luz por canal R/G/B do doador |
| `background.offsetRgb` | do cache, senão `[0,0,0]` | Correção aditiva R/G/B do doador, em valores RGB 0..255 |
| `background.featherPx` | 0 | Sigma **adicional** sobre a máscara do remendo existente; zero preserva seu feather original |
| `background.patchOffsetPx` | `[0,0]` | Desloca a máscara do remendo, em pixels do alpha, sem mover o vídeo doador |

**Regra confirmada por Lucas, reforçada em 17/10/2026:** o retalho de fundo deve ter feather espacial **bem suave**, sem emenda perceptível. Conferir o contorno inteiro do retalho no tamanho de uso e em detalhe, no início/meio/fim e em movimento; a presença de uma rampa numérica não comprova suavidade visual. `background.featherPx: 0` somente preserva o feather da máscara, não garante que ele seja suficiente. Suavizar a máscara do retalho separadamente do alpha do cabelo, sem desfocar a imagem. Escolher e alinhar o doador para preservar linhas, textura e iluminação do fundo; feather não corrige um doador incompatível.

Ao encontrar perda do volume com a cobertura do retalho, revisar primeiro o seed/alpha do sujeito. Não usar uma proteção ampla de fundo para esconder um erro do contorno: isso pode devolver fios soltos, como ocorreu na cena 2 do 177. Corrigir e propagar novamente somente a cena afetada; conferir entrada com margem, trecho reportado e saída antes da produção.

Correção específica do 177: ampliar a limpeza pela lateral direita da cabeça da apresentadora (esquerda no vídeo), abaixo da região do topo que foi tratada na v1. Revisar a extensão por cena e preservar o volume principal, rosto e costuras/linhas da cortina. Não tornar essa geometria uma regra para outros vídeos.

Os dois feathers são independentes. No 174, o alpha é 704 × 960: 0,6 px equivale a 1,2 px nativos. Mudar a resolução de saída não muda esses valores. Mudar a resolução de análise exige recalibrar as medidas e revisar a borda.

Ordem: níveis/gamma → expansão/contração → feather do cabelo → proteção de opacos e máscara manual → mistura entre ajustes de trecho → intensidade/bypass → recomposição com o remendo fixo. A forma de onda da transição do remendo é suavizada separadamente. RGB da pessoa sempre vem da fonte, sem foreground previsto pela rede.

**Proteção opaca limita a contração:** com `protectOpaque: true`, ela pode remover transparências da borda, mas não cortar pixels que a máscara original já considera opacos. Desativar torna a contração plena e pode reduzir volume. Usar apenas com revisão. Níveis agressivos também podem retirar partes semitransparentes reais; o padrão escolhido no 174 deixa níveis neutros e protege o alpha original com feather externo.

## Ajustes por trecho e bypass

Exemplo para editar a entrada de uma cena no JSON gerado (valores ilustrativos, não um novo padrão aprovado):

```json
{
  "alpha": {"featherPx": 0.8},
  "background": {"featherPx": 4},
  "intervals": [
    {"from": 40, "to": 80, "fadeFrames": 12,
     "alpha": {"offsetPx": 0.5}, "intensity": 0.7}
  ],
  "bypass": [{"from": 150, "to": 175, "fadeFrames": 12}]
}
```

Frames são locais à cena, intervalo semiaberto `[from,to)`. A configuração do intervalo vale integralmente dentro dele; rampas smoothstep acontecem nos frames anteriores/posteriores. As rampas terminam no corte e nunca usam frames de outra cena. Ajustes e suas rampas não podem se sobrepor; combinar conscientemente os parâmetros em um intervalo só. Bypasses podem se sobrepor e reduzem a intensidade multiplicativamente.

Fundos só admitem ajustes nos níveis global/cena: `background` dentro de um intervalo é recusado. Assim o agente não vincula acidentalmente o fundo ao movimento da cabeça. Para uma câmera realmente móvel, este método de doador fixo precisa de outra estratégia e nova validação; não habilitar deslocamentos temporais improvisados.

Se o doador sair da cobertura armazenada em `donorRoi`, a configuração é recusada. Preparar uma janela doadora maior; não repetir ou esticar pixels da borda silenciosamente.

## Analisar outro vídeo

Preparar um plano com `schemaVersion: 1`, `project`, `model` e `scenes` na ordem do corte. Paths relativos são resolvidos em relação ao plano. A análise não adivinha a região limpa do fundo, o contorno inicial nem as oclusões: o agente deve inspecioná-los no vídeo.

```json
{
  "schemaVersion": 1,
  "project": "/CAMINHO/editor/jobs/ID/project.json",
  "model": {
    "code": "/CAMINHO/MatAnyone2-main",
    "weights": "/CAMINHO/matanyone2.pth",
    "device": "mps"
  },
  "scenes": [{
    "id": "ID-1",
    "source": "/CAMINHO/bruto.mov",
    "seed": "/CAMINHO/seed-primeiro-frame.png",
    "roi": [400,1300,1408,1920],
    "alphaSize": [704,960],
    "fullSize": [720,1280],
    "donorRoi": [400,1040,1408,2180],
    "donorSize": [704,1090],
    "detailBox": [60,50,584,420],
    "patchMask": "/CAMINHO/remendo.png",
    "background": {
      "donorOffsetNative": [4,260],
      "offsetRgb": [0,0,0]
    },
    "protection": []
  }]
}
```

As coordenadas acima demonstram o formato, não devem ser copiadas para outra gravação sem inspeção. `roi` e `donorRoi` usam `[x,y,largura,altura]` nativos. `detailBox` usa pixels da janela de alpha. Todo o cabelo relevante deve caber na janela; mudanças grandes de posição exigem nova preparação.

`seed`: PNG binário 8-bit, 0/255, tamanho `alphaSize`, sujeito no primeiro quadro da cena. `patchMask`: PNG cinza 16-bit, mesmo tamanho, com o feather desejado e zero nas quatro bordas; também aceita NumPy float32 `.npy` sem pickle. `protection`: opcional, PNGs 16-bit para preservar mechas/rosto/objetos explicitamente marcados. Pode ter uma máscara fixa ou exatamente uma por quadro; uma máscara fixa não acompanha a cabeça. Proteção é aplicada por máximo ao alpha e permanece opaca onde o desenho é 1.

```sh
"$HAIR_PY" scripts/hair_analyze.py \
  --plan /CAMINHO/analysis-plan.json --out /CAMINHO/cache-novo

# Gera cache.json, controls.json, inference.json e entradas lossless.
"$HAIR_PY" scripts/hair_finish.py render \
  --cache /CAMINHO/cache-novo/cache.json \
  --config /CAMINHO/cache-novo/controls.json \
  --project /CAMINHO/editor/jobs/ID/project.json --out /CAMINHO/revisao-nova
```

V1 recebe cortes a 60 fps de fonte Rec.709 próxima de 60 fps; a preparação normaliza a grade conforme o projeto. Formatos de outra taxa/cor exigem adaptação explícita, não mudança silenciosa dos defaults. A análise usa memória nova por cena e dez repetições de aquecimento. Nenhuma máscara de outro vídeo é reutilizada automaticamente.

A fonte deve ter faixa limitada, pixels quadrados, sem rotação pendente e um áudio AAC ou PCM16 estéreo 48 kHz. PCM24/float é recusado em vez de reduzido silenciosamente. A conversão do doador fixa `format=bgr24` antes do empacotamento lossless: a negociação direta para BGRA mudou valores de cor na primeira migração, detectada e corrigida no teste de paridade.

Os vídeos preparados recebem timestamps a partir de zero depois do filtro de fps, com passagem explícita dos quadros. A migração v11 conserva sua sequência RGB exata. Trechos parciais decodificam o prefixo em vez de usar seek por frame, evitando diferenças de um quadro causadas pelo arredondamento de timestamps do Matroska.

`hair_finish pack --plan ... --project ... --out cache.json` permite empacotar máscaras já produzidas, sem nova inferência. O plano preparado contém `binding` igual a `hair_controls.edit_binding(project)` e, por cena, `source`, geometrias, `roiVideo`, `fullVideo`, `donorVideo`, `alphaDir`, `patchMask`, `background`, `protection`. Alphas são PNGs cinza 16-bit `0000.png` em diante, um por frame. Vídeos preparados são CFR 60 fps alinhados desde o frame zero da cena; o vídeo completo contém PCM16 estéreo 48 kHz. Exemplo real: `analysis/hair-validation/controls-v12/cache-final/plan.json`.

## Cache, saídas e invalidação

- O cache registra hash real da fonte, vínculo de cada cena ao mediaId/inFrame/duração, fps, geometria, modelo, seeds e todos os arquivos derivados. O render verifica os arquivos antes/depois. As máscaras originais nunca são gravadas pelo render.
- O hash integral do bruto é conferido ao preparar/empacotar. A recomposição lê e verifica os derivados selados, podendo trabalhar com o bruto offline; não recalcula o hash do bruto a cada ajuste. Uma troca de fonte deve ser registrada com seu novo mediaId no harness, que continua responsável pela reconexão/verificação do original antes da produção.
- Fonte/corte/ordem/seed/modelo/ROI alterado: refazer ou realinhar a análise explicitamente. Mudar legendas/stills sem mudar o corte não invalida o alpha. O comando recusa cortes incompatíveis mesmo que a duração total seja igual.
- Alterar controles: somente recompor. A configuração recebida é copiada para a nova saída, com hash. Resultados anteriores e cache não são substituídos. Um `failed.json` indica falha; só `report.json` com `technicalPass: true` confirma conclusão técnica.
- Saídas: `result.mp4`, `result-pcm.mov`, `comparison.mp4`, `edges.mp4`, `masks.mp4`, `audio.wav`, `config.json`, `metrics.json`, `report.json`. `--save-masks` grava alphas ajustados; os originais continuam no cache.
- Sem base anterior, o MOV conserva PCM16 do cache bit a bit; MP4 usa AAC. Com `--base-video`, o MOV conserva PCM16/24/float32 da base anterior, no mesmo formato e com comparação de todos os bytes decodificados. A análise original continua independente do acabamento facial.
- Rec.709 é explícito na entrada/saída, mistura em RGB8 decodificado, como na amostra aprovada. Não há tone mapping ou linearização. Prévia usa H.264; `--quality production` gera também a base `result-pcm.mov` em ProRes 422 Standard, exigindo cache na resolução do projeto. É um intermediário, nunca uma liberação de master. A recomposição RGB8 não preserva precisão superior da base ProRes; a preservação de pixels protegidos é medida antes da codificação nessa representação, não como igualdade de bytes entre dois ProRes.

`cacheId` sela caminhos e hashes; ao realocar os arquivos, preparar um novo manifesto com os mesmos conteúdos verificados. Cache e controles são artefatos explícitos. O snapshot padrão do harness não inclui automaticamente arquivos arbitrários em `analysis/`; preservar esses diretórios/configurações junto ao material da edição.

## Fluxo integrado por job

Fonte de verdade: `Edit/<id>/project/finishing.json → hair`. Configuração completa fica dentro do documento, incluindo `defaults`, ajustes `scenes.<id>`, intervalos e bypass. Por isso checkpoints e forks guardam os controles junto ao job. A configuração não altera `videoMediaId` (acabamento anterior), `audioMediaId`, ganho, maquiagem, legendas ou stills.

```sh
# Usar cache existente. Valida vínculo e arquivos, copia controles para o job.
# Fica configurado, mas só hair-attach ativa um resultado verificado.
.venv/bin/python scripts/studio.py hair-setup 174 \
  --cache analysis/hair-validation/controls-v12/cache-final/cache.json \
  --config analysis/hair-validation/controls-v12/defaults-final.json

# Para uma gravação NOVA, preparar seeds/ROIs/doador no plano acima e usar:
.venv/bin/python scripts/studio.py hair-prepare ID \
  --plan /CAMINHO/plano.json --work /CAMINHO/analise-v01
# --python /CAMINHO/venv/bin/python é opcional em setup/prepare.
# Modelo local e revisão manual das entradas continuam necessários.

# Exportar a configuração atual, editar defaults/cenas/trechos, importar.
.venv/bin/python scripts/studio.py hair-config 174 --out /CAMINHO/ajustes-v02.json
.venv/bin/python scripts/studio.py hair-config 174 --config /CAMINHO/ajustes-v02.json

# Testar trecho: frames locais, fim exclusivo. Não pode ser ligado à timeline inteira.
.venv/bin/python scripts/studio.py hair-render 174 \
  --work /CAMINHO/teste-v02 --scene 174-1 --frames 0:120 --save-masks

# Corte completo e associação para a prévia normal do editor.
.venv/bin/python scripts/studio.py hair-render 174 --work /CAMINHO/completo-v02
.venv/bin/python scripts/studio.py hair-attach 174 --work /CAMINHO/completo-v02
.venv/bin/python scripts/studio.py render 174 --out /CAMINHO/editor-previa-v02.mp4

# Desativar conserva controles, cache, histórico e resultado; volta à base anterior.
.venv/bin/python scripts/studio.py hair-disable 174
# Para reativar um resultado ainda válido, usar hair-attach novamente.
.venv/bin/python scripts/studio.py hair-status 174
```

Todos os diretórios/exports de saída precisam ser novos. `hair-config --config` substitui a configuração completa, não aplica um patch parcial. Exportar antes de editar evita perder ajustes já existentes. `hair-setup`/`hair-prepare` substituem a configuração do cabelo e deixam a etapa desligada; o histórico guarda a anterior. Nenhum comando associa automaticamente o último render nem concede aprovação estética.

`status` e `overview` incluem cabelo: `not-configured`, `configured`, `needs-render`, `active-preview`, `active-production`, `disabled` ou `stale`, com o motivo. Ajustar os controles mantém o resultado anterior preservado, mas o torna desatualizado. Cabelo ativo desatualizado bloqueia compilação/render: recompor e associar, ou desligar explicitamente. Não há fallback silencioso para uma versão antiga.

### Ordem de composição e áudio

1. Fonte/corte original → análise MatAnyone e cache de alpha/doador.
2. Base do corte original **ou** vídeo já tratado em `videoMediaId` → recomposição do cabelo.
3. Resultado de cabelo → stills, legendas e demais camadas do editor.
4. `audioMediaId`, quando presente, continua sendo a fonte de áudio do editor, com sua configuração própria.

`hair-render` lê automaticamente a base tratada ligada ao job, valida sua procedência quando veio do conector facial e não chama o motor de maquiagem. Preserva seus pixels onde o remendo efetivo é zero; a composição usa `remendo × (1 − alpha) × intensidade`, com transformação espacial fixa. O doador é o vídeo original sincronizado do cache: iluminação acompanha o tempo, posição não acompanha a cabeça. Na transição semitransparente ocorre a mistura necessária. Correção de cor que também mudou o fundo pode exigir recalibrar a luz do doador.

A base anterior deve ter o mesmo corte, 60 fps CFR, aspecto igual, dimensões iguais ou maiores que a saída e PCM estéreo 48 kHz; não se amplia uma base pequena. Rec.709 limitado é obrigatório. O ProRes 422 Standard do editor usa o contrato de faixa limitada mesmo quando o ffprobe omite `color_range` no MOV/nclc; a política usada fica no relatório. Arquivos HDR ou com rotação pendente são recusados.

O áudio da base é conservado em `result-pcm.mov`, inclusive float32/24-bit. MP4s comparativos usam AAC. O conector não aplica ganho nem processamento vocal. Se o job tiver voz separada, o compilador mantém essa ligação; desligar cabelo não altera a voz.

### Vínculo, revisão e resolução definitiva

`work/request.json` fixa corte, formato, cache, controles, base anterior e hashes do código. `work/stage.json` liga esse pedido ao relatório e `work/render/` contém mídias e diagnósticos. `hair-attach` verifica hashes, PCM, frames/PTS, corte completo, parâmetros e base; registra somente `hair.output`. Não usar `attach-finish video` para esse resultado: ele substituiria a base anterior e perderia a separação das etapas.

Mudanças de fonte, corte/ordem ou geometria invalidam o cache. Mudanças nos controles, formato final, código de composição ou base facial invalidam a saída. Trocar só legendas, stills, voz ou ganho não exige nova análise/recomposição de cabelo. Configuração de cabelo muda o fingerprint de pós-produção. A aprovação visual continua nos checkpoints e na liberação da exportação exata; `technicalPass` e `hair-attach` não equivalem a aprovação de Lucas.

Com cache preparado na resolução definitiva, usar:

```sh
.venv/bin/python scripts/studio.py hair-render ID \
  --quality production --work /CAMINHO/cabelo-definitivo-v01
.venv/bin/python scripts/studio.py hair-attach ID --work /CAMINHO/cabelo-definitivo-v01
# Só depois dos checkpoints reais do job:
.venv/bin/python scripts/studio.py render ID --master --out /CAMINHO/master-v01.mov
```

Um resultado marcado `preview` é bloqueado em master, mesmo que alguém aumente as dimensões do projeto. O cache 720×1280 do 174 continua sendo amostra: preparar vídeos derivados na resolução definitiva e revisar bordas antes da produção. O alpha pode ter resolução de trabalho própria; sua preservação/reutilização deve respeitar o vínculo exato ao corte e a revisão na saída final. O teste técnico ProRes 1440×2560 não aprova a estética do vídeo completo nessa resolução.

Snapshots guardam a configuração e IDs de mídia; não embutem vídeos, máscaras, `stage.json` ou cache arbitrários. Preservar os diretórios de análise/render indicados e a biblioteca de mídia. Hashes conferem conteúdo, não são backup. Fork do mesmo corte conserva os ajustes; `assemble` de cenas cria acabamento novo e exige preparar/realinhar um cache compatível.

Não houve integração ou alteração no Rosto Natural. A disponibilidade técnica local do MatAnyone não muda os termos da licença dos pesos/código; o registro da licença consultada permanece na pesquisa v09 para eventual adoção comercial.

## Validação da implementação

```sh
"$HAIR_PY" -m unittest discover -s tests -p 'test_hair*.py' -v
pnpm check
pnpm test:harness
pnpm status
pnpm validate:final
```

Os testes numéricos requerem OpenCV; o ambiente básico os sinaliza como skipped, não como validação completa. Evidências reais e comandos da migração, paridade da v11, teste com ajustes e análise curta em `analysis/hair-validation/controls-v12/`. Os gates produtivos do 174 continuam pendentes; a aprovação da amostra de cabelo não libera o master.

Integração exercitada e relatório: `analysis/hair-validation/editor-integration-v13/`. A fixture de base anterior contém uma marca sintética deliberada; valida a ordem de composição, preservação e transporte de áudio, não a qualidade de uma maquiagem nova.

## Regressão de limite de fonte após migração

Na fixture CFR de 60 quadros, o filtro fps descartava o último quadro ao chegar ao EOF. A preparação agora fornece 50 ms de margem ao filtro e limita a saída ao número de quadros do corte previamente validado contra a duração da fonte. Comparação dos 60 quadros decodificados com a referência sem conversão de fps confirmou igualdade na fixture. Cortes além da duração continuam recusados; isso não autoriza estender fontes ausentes.
