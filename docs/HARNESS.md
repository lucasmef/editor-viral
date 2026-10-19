# Harness local — operação e retomada

> Estado operacional atualizado em 17/10/2026: [EDITOR_OPERACAO_ATUAL.md](EDITOR_OPERACAO_ATUAL.md). As descrições datadas abaixo preservam o histórico; capacidades atuais, comandos e limitações estão no índice vigente. Nenhuma atualização migra o 177.

> Fluxo editorial vigente: [preparação e Premiere](FLUXO_EDICAO_PREMIERE.md), aprovado em 15/10/2026. Este manual descreve comandos existentes; os novos requisitos de galeria, texto nativo, geometria das peças e entrega Premiere ainda exigem implementação/validação. Não confundir aprovação do fluxo com recursos já disponíveis.

Direção editorial habitual: [Padrão visual 101](PADRAO_VISUAL_101.md). Esse contrato separa regras fixas, variáveis por vídeo, valores atuais do 174 e perguntas necessárias quando faltar definição.

> Formato de acabamento definido por Lucas: tomadas com margens em 2160 × 3840, 60 fps, ProRes 422 Standard (perfil 2), nunca HQ ou LT. A entrega 1440 × 2560 é independente. Reextrair do bruto 4K; não ampliar acabamento menor. Contrato e limitações atuais em [acabamento com margens](../skills/raquel-video-editor/references/finishing-handles.md).
Entrada principal: `.venv/bin/python scripts/studio.py`. Dados por vídeo em `Edit/<id>/project/`; a biblioteca usa IDs SHA-256, independentes de nome/caminho. Rodar uma mutação por vez; os arquivos JSON são atômicos, mas esta versão não é um servidor multiusuário.

## Organização

Política de pastas e retenção: [ARMAZENAMENTO.md](ARMAZENAMENTO.md). Define as raízes externas oficiais Source/Assets/Edit/SoundFx/Cache/Prontos e o plano de migração; dados de jobs terão destino Edit/<id>/project e catálogo Edit/_editor/media.json. O reinício vazio do 174 é histórico; consultar o estado real e preservar os ajustes atuais. Pesquisa legada foi retirada do editor; não é uma edição ativa. Fonte de raízes: studio/storage.json.

Acabamento facial local: [ROSTO_METAL.md](ROSTO_METAL.md) documenta `face-base`, `face-prepare`, `face-render` e `attach-finish --face-run --temporal-review`. A base segue o corte atual sem overlays; áudio tratado e camadas permanecem separados. A associação verifica procedência e não concede aprovação.

- `project.json`: cenas, cortes, camadas, eventos e legendas locais à cena; schema 2.
- `brief.json`: intenção, roteiro, referências e restrições.
- `looks.json`: alternativas e escolhas; estados não equivalem a aprovação automática.
- `style.json`: cópia versionada do perfil aplicado ao vídeo; mudar o padrão do estúdio não muda projetos antigos.
- `finishing.json`: ganho e ligações com áudio/vídeo tratados.
- `history/`: eventos datados, sem sobrescrita; `revisions/`: snapshots com hashes e cópia do código/lockfile.
- `approvals/`: decisão, responsável, fingerprint da etapa e hash da evidência.
- `releases/`: aprovação final ligada ao hash exato do master e relatório.
- `STATUS.md`: resumo regenerável com `overview`, nunca fonte de dados.
- `Edit/_editor/media.json`: catálogo de mídias e localizações. `Assets/_catalog/`: cópias persistentes dos stills.

Não guardar o único original em cache. Backups devem incluir projetos de Edit, catálogo, código/lockfile, assets e localização dos originais. O arquivo final sozinho não preserva camadas. Projetos/documentos não vão automaticamente para Git, Pages ou nuvem.

## Comandos comuns

```sh
# Novo projeto e diagnóstico
.venv/bin/python scripts/studio.py init 175 --brief 'Descrição do vídeo'
.venv/bin/python scripts/studio.py status 174
.venv/bin/python scripts/studio.py overview 174

# Salvar uma versão antes de decisões ou alterações
.venv/bin/python scripts/studio.py checkpoint 174 --note 'Descrição e motivo da decisão'

# Prévia e teste parcial
.venv/bin/python scripts/studio.py render 174
.venv/bin/python scripts/studio.py render 174 --frames 0-119
.venv/bin/python scripts/studio.py render 174 --cut-only

# Checar condições de master; falha enquanto estiver pendente
.venv/bin/python scripts/studio.py gate 174
.venv/bin/python scripts/studio.py render 174 --master
```

Sem --out, render cria Edit/<id>/reviews/<execução>/preview.mp4 ou candidates/<execução>/master.mov; compile grava um JSON em Cache/<id>. --out continua disponível, mas recusa saídas dentro do editor, em Source ou em Prontos antes da liberação. Saídas e registros não são sobrescritos. Falha de render pode deixar manifesto/log para diagnóstico: usar outro nome na tentativa seguinte. O public-dir de cada render contém cópias somente das mídias utilizadas; links simbólicos não são confiáveis no empacotamento do Remotion.

`video_harness.py` continua fornecendo probe, validação estrutural e verificação de codec. Seu antigo `render --final` foi desativado para produção: os booleans antigos não liberam masters. Testes técnicos `RawCheck`/`ExportCheck` não são aprovações de conteúdo.

`render --cut-only` prepara uma prévia do mesmo corte sem camadas, rótulos e legendas. Não altera o projeto editável e não combina com master. O relatório registra `cutOnly`. Para comparar até três propostas de apresentação num mesmo frame de cena, usar `scripts/sample_styles.py JOB --scene CENA --frame FRAME_LOCAL --options OPCOES.json --out DIRETORIO_NOVO`. Cada opção contém `label` e `layout`; gera PNGs e manifestos compilados imutáveis, sem alterar o estilo do job ou aprovações. Estes arquivos são evidências, não uma segunda timeline editável.

## Escolha das tomadas antes do corte justo

Implementado no modelo em 15/10/2026 durante a preparação do 177: um player por cena, todos os takes em sequência, botões de salto por tomada, rótulo do take atual e transcrição. Tentativas incompletas continuam acessíveis e sinalizadas. Navegar/reproduzir não seleciona nem aprova; manter confirmação pelo servidor oficial e IDs/intervalos de origem. Os limites entre tentativas devem ser explícitos.

Fluxo solicitado por Lucas em 14/10/2026: transcrever → organizar tentativas por cena → Lucas escolhe no HTML → refinar cortes pela waveform → devolver corte para revisão. A seleção não concede aprovação de preproduction e não ativa Voz Neural, rosto ou cabelo.

Modelo reutilizável: `studio/templates/takes-review.html`. Gerador: `scripts/takes_review.py`. O agente prepara `Edit/<id>/project/take-candidates.json` com `job`, `scenes[{id,label,script,takes[{id,label,complete,mediaId,start,end,transcript}]}]`; tempos em segundos do original. Fonte de verdade da escolha: `project/take-selection.json`, criada somente quando o usuário confirma no servidor local. O manifesto e previews da galeria ficam no diretório externo de revisão. Não são outra timeline.

```sh
.venv/bin/python scripts/takes_review.py build 174 --input /CAMINHO/Edit/174/project/take-candidates.json --out /CAMINHO/Edit/174/reviews/takes-v1
.venv/bin/python scripts/takes_review.py serve 174 --directory /CAMINHO/Edit/174/reviews/takes-v1
```

Abrir o endereço local retornado (com token). Seleções ficam em rascunho no navegador até **Confirmar escolhas**. Após salvar, Lucas volta ao chat para pedir continuação; não existe processamento automático. `file://` também funciona para assistir/selecionar, mas a confirmação baixa um JSON que precisa ser enviado no chat. Copiar escolhas é outra opção. Não alegar que um clique em arquivo HTML gravou no projeto. O servidor escuta somente em 127.0.0.1; não publica nem envia mídia.

Após receber escolhas, conferir IDs e hash do manifesto, inclusive se uma tentativa parcial foi selecionada. Preparar nova revisão do corte com as tomadas escolhidas e analisar waveform do áudio original. Inspecionar entradas/saídas e pausas; remover silêncios excessivos sem cortar sons fracos, consoantes, finais e respirações necessárias. Registrar tempos novos e remapear legendas/eventos. Não executar remoção cega por limiar. Exportar `render --cut-only` para avaliar o corte refinado. Não herdar aprovação ou acabamento da proposta anterior.

## Checkpoints de aprovação

Checkpoint editorial obrigatório antes de separar peças: mostrar o look completo recebido, apenas sem fundo, sobre o vídeo com guias. Lucas aprova tamanho e localização; só depois separar/reconstruir componentes. Registrar referência/hash, transformação e decisão real; aprovação de layout não aprova os recortes posteriores. Este requisito não cria automaticamente um novo gate no código. Ver [fluxo vigente](FLUXO_EDICAO_PREMIERE.md).

1. `preproduction`: corte inicial + escolhas de looks.
2. `production`: sincronização com gesto/fala, stills, legenda e composição.
3. `postproduction`: áudio, cor e retoque aplicável.
4. `release`: reprodução completa e aprovação da exportação exata.

Para registrar aprovação, preparar evidência JSON que documente uma revisão realmente feita. Exemplo estrutural, não uma aprovação pronta:

```json
{
  "fingerprint": "COPIAR_DO_STATUS_DA_ETAPA_REVISADA",
  "userApproval": "Referência à mensagem real de Lucas/Raquel e seu escopo",
  "notes": "O que foi examinado; intervalos; decisões e limitações",
  "checks": {"cuts": "passed", "looks": "passed"}
}
```

```sh
.venv/bin/python scripts/studio.py approve 174 preproduction --evidence CAMINHO.json --reviewer Lucas
```

A etapa seguinte exige a anterior válida. Evidência alterada invalida a aprovação. `production` exige gestures/captions/stills/visual; `postproduction`, audio/color/retouch. Não usar `not-applicable` para evitar revisão necessária. Marcar não aplicável só para dimensão ausente, explicando nas notas. Nunca preencher userApproval por inferência a partir de “faça uma prévia”.

O ganho/tratamento de áudio altera o fingerprint de pós-produção. Cortes/ordem/looks planejados alteram pré-produção e etapas posteriores. Mudanças de composição/legenda/motor alteram produção e pós. Os hashes detectam mudanças, não avaliam gosto ou substituem escuta real. Não há isolamento de permissões contra alguém que reescreva o próprio programa ou os registros.

O master é primeiro um candidato tecnicamente verificado. Para liberar, a evidência final contém `outputSha256`, `userApproval`, `notes` e checks visual/audio/completePlayback = passed:

```sh
.venv/bin/python scripts/studio.py release 174 --out /CAMINHO/Edit/174/candidates/EXECUCAO/master.mov --evidence REVISAO-FINAL.json --reviewer Lucas
```

O comando revalida os checkpoints, hashes do arquivo/manifesto e decodificação/preset. Não altera o master; copia os bytes verificados para Prontos/<id>/<revisão>-<hash>/, sem sobrescrever e sem colocar sidecars em Prontos. Nenhum master do 174 está aprovado até agora.

## Brutos offline e reconexão

```sh
.venv/bin/python scripts/studio.py register '/pasta/IMG.MOV' --kind original --archive 'localização conhecida do arquivo de segurança'
.venv/bin/python scripts/studio.py relink MEDIA_ID '/novo/caminho/IMG.MOV'
.venv/bin/python scripts/studio.py relink MEDIA_ID '/backup/IMG.MOV' --verify-archive
.venv/bin/python scripts/studio.py archive-check MEDIA_ID
```

Nome igual não basta: o SHA completo precisa corresponder. Arquivo convertido requer novo registro e alinhamento explícito. `--archive` guarda um endereço informado, não comprova backup. `--verify-archive` confere bytes de uma cópia acessível; isso não prova retenção na nuvem ou independência física do disco.

Não existe comando de apagar mídia. Liberar armazenamento deve remover somente uma cópia local após verificar a cópia arquivada e entender a sincronização do serviço. O harness não baixa arquivos da nuvem: baixar pelo armazenamento escolhido e executar relink. Nenhum original foi removido neste trabalho.

Prévia prefere o proxy do clipe e permite original offline. Proxy registra o primeiro frame correspondente no original; aparar o início mantém o alinhamento. Estender além da cobertura do proxy exige original online. Master usa originais e nunca promove automaticamente o proxy ao master. Criar proxies adicionais ainda usa FFmpeg; o cadastro e a relação com o clipe devem registrar o intervalo exato.

## Reeditar e mesclar

```sh
.venv/bin/python scripts/studio.py fork 174 REVISAO 174-v02
.venv/bin/python scripts/studio.py assemble remix-174-176 174:REVISAO:CENA 176:REVISAO:CENA
```

`fork` restaura os documentos da revisão em um novo projeto e mantém o anterior intacto. Informa se o motor atual diverge do arquivado; a cópia do motor fica disponível, mas não é reinstalada/executada automaticamente. Revalide a nova edição nesse caso. Aprovações não são copiadas.

`assemble` aceita cenas de snapshots verificados, guarda procedência, remapeia tempos globais a partir dos tempos locais e recusa formatos/estilos diferentes. Tratamentos de áudio/vídeo completos não são herdados: pertencem à montagem anterior. O motor não faz adaptação criativa silenciosa entre estilos.

Para apenas mudar a ordem, reordenar o array de cenas do projeto de trabalho e salvar checkpoint com motivo. Não alterar snapshots: adulteração é detectada.

## Contrato de cena

`clip.inFrame` e `duration` usam a base de fps do projeto; o original é identificado por `mediaId`. Proxy opcional: `{mediaId, inFrame, sourceInFrame}`. `sourceInFrame` é o tempo original correspondente ao inFrame do proxy, na mesma base do projeto. Tempos em segundos são convertidos explicitamente na importação.

Camadas têm `mediaId`, retângulo e entrada/duração locais. Eventos: `{id,kind:"gesture"|"word",frame}`. Camada com `anchor` aponta ao evento e aceita `offsetFrames`; a duração vai até o fim da cena. A ferramenta valida intervalo, mas não detecta automaticamente o pompom. A marcação do gesto precisa ser revisada visualmente.

Legendas têm texto, from/duration locais e highlight opcional. `caption_rules.py` filtra apenas a exibição, mantendo os timestamps das palavras e preservando negações; conservar transcrição integral. A política de palavra por palavra é verificada no master. A aparência do destaque ainda deve ser calibrada e implementada numa amostra aprovada — não é confundida com o planejamento de texto.

## Integração de acabamento

Cabelo local com MatAnyone 2: ver [HAIR_FINISHING.md](HAIR_FINISHING.md). `hair-prepare`/`hair-setup` vinculam análise ao job; `hair-config` ajusta níveis, contract/expand, feathers, intensidade e bypass por vídeo/cena/trecho. `hair-render` recompõe; `hair-attach` liga a etapa separada, e `hair-disable` restaura a base anterior. Configuração em `finishing.json → hair`, incluída em snapshots/status. Vídeo facial e voz permanecem independentes; amostras não entram em master. Ver o contrato e os comandos no documento de cabelo.

```sh
.venv/bin/python scripts/studio.py attach-finish 174 audio '/saida/voz.wav' --notes 'Processador/preset/versão e revisão de alinhamento'
.venv/bin/python scripts/studio.py attach-finish 174 video '/saida/base-tratada.mov' --notes 'Processador/preset/versão e revisão temporal'
```

Entrada é o resultado do corte completo, sem textos/stills queimados. O áudio substitui a voz original, não toca duplicado; ganho volta a 0 ao ligar áudio tratado. Vídeo tratado substitui só a base, mantendo overlays editáveis. Duração e vínculo com o corte são conferidos. Se mudar ordem/cortes, o material tratado é recusado até ser refeito/realinhado. Mesma duração não prova sincronismo perceptivo: revisão continua obrigatória.

Voz Neural: novos jobs recebem o preset aprovado e o áudio é preparado automaticamente por `render`/`compile` após aprovação de preproduction. Cortes alterados exigem novo processamento; ganho adicional zero. Ver [VOZ_NEURAL.md](VOZ_NEURAL.md). Rosto Natural possui conector local explícito; gradação e efeitos sonoros não foram ativados automaticamente. Ver `INTEGRACOES.md`.

## Revisão look por look (opcional)

Pode ser usada para revisar um único look ou todos. Cadastrar IDs como `174-1:girl` e `174-1:boy` quando a nova montagem existir. O 174 reiniciado ainda não tem cenas nem looks.

A revisão individual é de produção: styling, recorte, composição e timing das entradas. Cada look aponta às suas camadas por `scene.looks = [{id,label,layerIds}]`. A base e os acessórios continuam independentes. `status` / `overview` apresentam estado e fingerprint de cada look.

```sh
# Prévia da primeira combinação inteira, para avaliar o girl ou boy em contexto
.venv/bin/python scripts/studio.py render 174 --scene 174-1

# Registrar a decisão real sobre apenas o girl
.venv/bin/python scripts/studio.py review-look 174 174-1:girl --evidence REVISAO-LOOK.json --reviewer Lucas
```

A evidência inclui fingerprint do look, userApproval, notes e checks styling/cutout/composition/timing. Todos os checks precisam ser passed para aprovar. `--decision rejected` registra pedido de correção sem exigir checks aprovados. É possível registrar referências a frames/intervalos e observações nas notas.

Mudanças nas camadas do boy invalidam sua revisão, preservando a do girl. Mudanças compartilhadas em corte, duração, roteiro, eventos, legendas, estilo ou motor invalidam as revisões afetadas. Se um atlas inteiro é regenerado, o ID do arquivo muda e todos os looks que o usam precisam ser revistos. A revisão individual não certifica retoque/áudio de pós-produção nem a interação posterior com outro look alterado: a revisão global continua necessária.

`project.requireLookReview = true` torna as revisões dos looks cadastrados obrigatórias antes de aprovar produção/gerar master. Deixar false permite acioná-las somente quando necessário; esse é o comportamento padrão. Nesse modo, uma revisão individual pendente não bloqueia automaticamente a aprovação global, que deve resolver explicitamente o escopo revisado. Ao ativar o modo obrigatório, cadastrar todos os looks que serão examinados.

`--scene` seleciona automaticamente o intervalo de frames atual, incluindo fala, legendas e ambos os lados. Não combina com --frames ou --master. Não corta fora o outro lado para evitar esconder colisões de layout. Reordenar cenas recalcula o intervalo. Nenhuma soma de aprovações individuais libera o arquivo final: ritmo, transições, voz e playback completo permanecem checkpoints globais.

## Som pontual e cor da base

`finishing.json.soundEffects` admite cues `{mediaId, scene, frame, duration, gainDb}`. `scene` é o segmento editável, frames são locais, duração em frames; ganho independente entre −60 e 0 dB. O compilador remapeia após reordenação, valida limites e inclui os sons no snapshot/staging. Registrar o WAV em SoundFx. Entradas pelo pompom exigem evidência visual, não basta texto ASR. Não altera o preset ou ganho da voz. `--cut-only` omite esses cues.

`finishing.json.colorGrade` admite multiplicadores `brightness`, `contrast`, `saturation` (0,5..1,5; identidade 1). Aplicação visual somente à base, depois de rosto/cabelo; roupas e legendas mantêm as cores próprias. Controles ausentes preservam o comportamento anterior. O renderer mantém Rec.709; isso não é conversão HDR.

`render --preview-scale 1` gera uma prévia H.264 na resolução integral do projeto, para revisão de composição e acabamento. O padrão continua 0,5. Esta opção é exclusiva de prévia: não aprova checkpoints, não cria master ProRes e não libera Prontos. Produção final permanece em `render --master` e `release` após decisões reais de revisão.

## Revisão de recortes antes da montagem

Após corte aprovado e referências escolhidas, preparar os recortes de todas as cenas e a revisão estática descrita em [contrato de recortes](../skills/raquel-video-editor/references/cutout-production.md). Aguardar confirmação explícita de Lucas dos arquivos identificados por hash antes de associar os looks à montagem. Manter mapa de componentes no job externo e evidências em reviews; referências e PNGs em Assets.

Este é um checkpoint operacional solicitado por Lucas, anterior à montagem, e não um novo comando `approve` implementado no harness. O estado `preproduction: approved` não comprova aprovação dos recortes. Não simular essa aprovação usando `review-look`, que revisa looks já montados, nem afirmar bloqueio automático pelo software. Registrar decisão real com escopo e hashes no histórico/evidência externa.

Sequência confirmada por Lucas: escolher takes → aprovar vídeo completo com cortes justos → enviar imagens → aprovar recortes de todas as cenas → montar e continuar etapas. A aprovação dos recortes autoriza iniciar a montagem sem repetir a pergunta; não equivale à aprovação da exportação. Cintos e calçados usam encaixe contextual e máscara local conforme o contrato de recortes, preservando a mesma base.

Na preparação dos recortes, cada acessório distinto tem arquivo e coordenadas próprios. Casacos abertos exigem imagem completa com forro, peça interna inteira e frente derivada por máscara da mesma imagem completa. Preservar a relação por hash e verificar a recomposição antes/depois da blusa; consultar o contrato de recortes para a ordem e as máscaras. As prévias estáticas não registram aprovação automaticamente.

## Margens para ajuste posterior do corte

Direção atualizada em 15/10/2026: reservar janelas ampliadas ao escolher as tomadas e tratá-las após aprovação do corte justo: preferencialmente 1 s real no início e 1 s no fim de cada cena, com 0,5 s como alternativa quando a janela útil for menor. Registrar a disponibilidade efetiva. Após mudar a ordem, rever cada junção e ajustar o intervalo usado para evitar a combinação de saída seca e entrada brusca; as margens são reserva, não pausas obrigatórias. Método e contrato: [acabamento com margens](../skills/raquel-video-editor/references/finishing-handles.md). Os comandos `window-init`, `--window-work` nos conectores e `window-publish` implementam janelas visuais de maquiagem/cabelo em 4K, selecionadas na compilação por origem e intervalo. O modo legado e a voz ainda validam o corte inteiro; reconformação da voz permanece pendente. Preservar os bloqueios de áudio/rosto/cabelo incompatíveis e as versões anteriores.

## Enquadramento da apresentadora e abertura limpa

`style.json → layout.base` admite `{scale, x, y}` para reenquadrar somente o vídeo tratado, preservando a fonte 4K. Escala de 1 a 1,5; deslocamentos em pixels da composição são limitados para não expor bordas. Não altera máscaras, áudio ou o corte original. Validar visualmente rosto, mãos e sobreposições.

`layout.revealOverlaysWithLooks: true` mantém rótulos e legendas ocultos até a primeira entrada de camada em cada cena. Os looks devem ter `from` maior que zero quando a abertura precisa estar limpa. Marcar gestos pela inspeção visual de quadros consecutivos e registrar evidência local por cena; usar o mesmo frame para entrada e cue de clique em `soundEffects`. Não confundir tempos de ASR/palavras com marcação do pompom. As coordenadas calibradas pelo 101 pertencem ao estilo do job 174, não aos padrões globais.

## Guias de segurança e altura dos looks

Regra de Lucas (14/10/2026), para este e próximos vídeos: reservar **6% da largura à esquerda e à direita e 6% da altura em cima e embaixo**. A área segura é 88% × 88%. Em 1440×2560: x=86,4..1353,6; y=153,6..2406,4. Peças, acessórios e textos devem ficar dentro dela; a imagem de fundo continua preenchendo a tela.

Toda prévia compilada recebe `previewGuides` e mostra o retângulo ciano de segurança, inclusive `--cut-only`, `--scene` e `--preview-scale 0.5`. As guias são parte da imagem da prévia, não apenas do HTML, e não desaparecem na abertura limpa. Masters recebem `previewGuides: null`: guias técnicas não entram na entrega final.

A altura de referência dos looks é separada da área segura. `style.json → layout.lookGuides = {top,bottom}` usa frações da altura, específicas do job. Medir em frame real escolhido: topo da roupa (gola/ombro, sem óculos ou boné) e barra da calça (sem sapatos). Registrar frame, referência, coordenadas e evidência. Não usar limites de todo o PNG, que incluem acessórios, nem deformar roupas para caber. Linhas amarelas ficam visíveis em todas as prévias do job. Essas guias orientam a calibração; não significam ajuste automático/aprovação dos looks. O 101 é referência do 174, não uma altura universal para todo vídeo.


### Cor da base e destaque discreto

`finishing.colorGrade` afeta somente o vídeo gravado: brightness/contrast/saturation e warmth (0–0,3, tonalização sépia suave). Nunca aplicar o filtro no contêiner que reúne looks, labels e legendas. O ajuste não cria luzes ou objetos. `caption.highlight: glow` mantém tamanho, posição e contorno normais, acrescentando somente brilho branco, sem escala animada. Labels com `bubble: true` usam letras arredondadas, contorno branco e sombra; a posição fica no estilo do job. No 174, referências fornecidas por Lucas em 14/10/2026 estão preservadas no diretório externo de revisão; escolha de referência não aprova automaticamente a exportação.

Labels também podem usar `mediaId`, `width`, `height` e `crop` para lettering em PNG transparente fiel à referência. O compilador resolve o asset e o inclui no catálogo de dependências e no diretório isolado do render; não substituir lettering ilustrado por uma fonte genérica sem conferir o resultado. O estilo do job permanece com mediaId, sem paths compilados. A revisão do 101 em 14/10/2026 (3,6–3,8 s, palavra “rico”) mostrou halo branco amplo e difuso, mantendo o contorno preto nítido; uma sombra estreita não reproduz esse efeito.

### Legendas contínuas

`style.captionPolicy.continuous: true` preenche lacunas entre palavras visíveis no ponto médio do intervalo. Os tempos originais permanecem em project.json. Na compilação, a primeira legenda começa no frame 1 do vídeo, as cenas seguintes começam no frame local 0 e a última palavra dura até o fim de cada cena. Verificar cobertura exata dos frames 1..N-1, sem sobreposição. A renderização das legendas não depende de `revealOverlaysWithLooks`: o pompom governa looks e títulos, não cria lacunas de legenda. A política de omissão e o destaque das palavras finais permanecem.

## Ajuste visual de peças no Remotion Studio — histórico, fora do fluxo atual

Comando: `.venv/bin/python scripts/look_studio.py 174 --port 3175` (trocar o ID). O launcher usa as dependências existentes, sem reinstalar, executa a CLI diretamente e mantém o servidor em 127.0.0.1. Não rodar pnpm na sessão temporária.

A partir da correção de 14/10/2026, os looks persistem propriedades nativas em `project.json → scenes[].layers[].native.props`. O mesmo `Interactive.Div` aplica essas propriedades na sessão e no renderer oficial: posição, escala por eixo, origem, rotação, opacidade, crop nos quatro lados, estilos estáticos e expressões de keyframes suportadas. O crop nativo é uma máscara visual separada do `crop` original de extração do PNG. Não substituir um pelo outro.

- Pausar no frame desejado, selecionar a peça na imagem/timeline e editar no Inspector. `⌘Z` desfaz; `⌘Y` refaz. Múltipla seleção altera as peças selecionadas. Frente/forro de casacos são camadas independentes, conforme solicitado.
- Entrada/saída, playback rate, trim, freeze, ocultar e duplicar/excluir peças são persistidos. Tempos devem permanecer na cena de origem. Edição de entrada/saída assume tempos manuais, removendo a âncora automática da peça. Isso não muda os cortes da apresentadora nem o áudio.
- Segurança de 6% e guias de topo/barra continuam visíveis. São referências, não travas de encaixe. Manter os elementos dentro delas ao revisar.
- Esperar **Salvo no projeto · controles nativos** antes de fechar. Toda gravação tem histórico antes/depois; o código pendente também é preservado em `project/studio-recovery/<sessão>/pending.tsx`. Erros não significam sucesso; a mensagem fica estável até desfazer/corrigir. Alterações externas bloqueiam a gravação para evitar sobrescrita.
- A reabertura recompila os controles salvos. O TSX da sessão é representação descartável somente quando todos os ajustes já foram importados. Projeto oficial e histórico ficam em Edit; sessão e proxy ficam em Cache.
- O navegador usa proxy; renderização da sessão usa `production.json` com as mídias de produção e exclui o aviso de salvamento. A exportação oficial continua pelo harness, com revisões/master/release. Não interpretar um render do Studio como master aprovado.
- Este editor é de peças existentes. Mudanças estruturais como adicionar nova mídia, pre-compose, HTML-in-canvas ou motion blur não têm importador e são rejeitadas explicitamente, com recuperação preservada. Não anunciar suporte irrestrito a todas as ações do Remotion. Legendas, base e títulos continuam governados pelo projeto/estilo, fora deste editor de peças. Ver `docs/STUDIO_INTERATIVIDADE.md`.

A organização das camadas do 174 foi mantida. Para próximos projetos, organizar a sequência principal e agrupar camadas por cena conforme a direção documentada.

## Intercâmbio programático com Premiere

Ver [Premiere XML](PREMIERE_XML.md) para exportar FCP7 XML com peças e áudio separados, limites das máscaras rasterizadas, snapshots e validação. Essa transferência não aprova o master nem altera o job original.


## Reprodução contínua das tomadas — correção de 16/10/2026

Um play reproduz todas as tomadas da mesma cena até o fim, incluindo interrompidas, em um único vídeo e uma única barra de tempo. Não depender da troca de arquivos no evento `ended`. Mostrar a tomada atual e sua transcrição conforme o tempo do player; os botões de salto apenas navegam. “Escolher tomada em reprodução” e os seletores individuais marcam a preferência sem parar o vídeo; “Confirmar escolhas” registra a decisão separadamente. Reprodução nunca seleciona automaticamente.

`scripts/takes_review.py build` prepara esse formato para novas galerias. Para atualizar uma galeria existente, usar `continuous ID --directory DIRETORIO`: preserva `manifest.json`, IDs, intervalos e hash das escolhas; adiciona vídeos por cena e `playback.json`, guardando o HTML anterior. Esta operação não altera a timeline nem aprova cortes. O servidor oficial permanece responsável pela confirmação.


### Galeria compacta — 16/10/2026

Uma cena por aba, vídeo grande limitado à altura disponível e painel lateral compacto com todos os botões de tomadas visíveis, sem carrossel horizontal. Play de todas as tomadas e escolha atual são controles pequenos e separados. O servidor suporta HTTP Range para saltos em vídeos ainda não baixados por inteiro; o salto aguarda metadados e entra 40 ms depois do limite para evitar arredondamento na identificação da tomada. Trocar de cena pausa a reprodução anterior. Escolhas explícitas feitas no chat podem ser registradas parcialmente, vinculadas ao mesmo hash do manifesto; não aprovam o corte. Na retomada, preservar escolhas locais ainda não confirmadas e carregar as decisões já registradas.
