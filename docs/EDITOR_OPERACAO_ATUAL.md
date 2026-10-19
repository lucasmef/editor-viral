# Operação vigente do editor — 17/10/2026

Este é o índice operacional atual. O projeto é **editor**; 174 e 177 são vídeos. Não migrar nem reexportar vídeos finalizados para atualizar o software. Os documentos antigos continuam úteis para decisões e contratos; descrições de capacidades pendentes datadas de 15/10 não substituem o estado abaixo.

## Retomada e fonte de verdade

`pnpm status ID` / `studio.py resume ID` lê o resumo sem renderizar, copiar mídia ou alterar o vídeo. Mostra histórico, registros de transferência, candidatos e relatórios legados. Sem registro novo, a presença de um relatório legado pede inspeção: não implica que se deva reiniciar a preparação nem inventar aprovação.

Antes da transferência, `Edit/ID/project` rege a preparação. Depois de `premiere-handoff`, o projeto `.prproj` e a sequência registrados regem a montagem. Alterações no Premiere são esperadas e aparecem como `edited-since-handoff`; o JSON não volta a ser uma timeline paralela. O estado técnico antigo de `studio.py status` continua disponível, mas seus checkpoints não descrevem sozinho uma montagem transferida.

`pnpm preview ID` e `pnpm validate:final ID` exigem ID explícito. Nenhum comando presume o vídeo 174.

## Fluxo completo

1. Galeria contínua: todas as tomadas, um player por cena, seleção separada do play.
2. Corte justo aprovado; reserva real preferencial de 60 frames em cada ponta, 30 quando necessário, exceções documentadas.
3. Acabamento em fontes 4K com reservas; voz por janelas pelo `voice_windows.py`. Não reutilizar voz conformada sem margens na transferência.
4. Qualidade e tamanho/localização dos looks completos aprovados, com segurança de 6% visível nas prévias.
5. Recortes recuperáveis, resolução original, comparação de todas as cenas e aprovação dos recortes.
6. Montagem: gestos marcados visualmente, dois estalos originais, legendas e grade somente na gravação.
7. Aprovação da prévia e autorização de transferência; pacote novo, importação XML, ajustes MCP com alvo explícito e conferência.
8. Conferência de geometria, texto, A/V e margens nos dois lados, mix/limitador, salvar/reabrir. Registrar transferência.
9. Exportação real pelo Premiere, candidato com procedência própria, revisão audiovisual do arquivo exato e liberação por SHA-256.

## Resolução e máscaras — correção explícita de Lucas

Nos próximos vídeos, **não reduzir a resolução das imagens ao passar PSD → PNG**. A escala da montagem pertence ao Motion do Premiere; não redimensionar o arquivo para o tamanho que ocupa no vídeo. Registrar dimensões originais e exportadas. Aparar apenas canvas vazio é permitido quando não reamostra pixels, registra offset em coordenadas originais e não quebra pares base/frente. Conservar canvas compartilhado nos pares mascarados.

**PNG alpha não é máscara editável.** Manter os pixels originais recuperáveis em PSD com camadas/máscaras ou no original acompanhado de máscara independente. Nunca apagar pixels para fazer o recorte, nem considerar um PNG transparente suficiente para recuperar áreas erradas. Guardar origem/hash, máscara, versão e evidência de leitura/reabertura. O 177 permanece intocado; a regra vale para produção futura.

Lucas autorizou PSD quando trabalhado por código, sem abrir Photoshop para edição manual. `scripts/psd_cutouts.py` lê PSD, aplica máscara em camada selecionada em **nova versão**, confere pixels e máscara ao reabrir e exporta PNG com canvas integral, sem resize. Adaptador atual: PSD RGB 8-bit, camada raster e máscara de usuário; recusa escrita em outros formatos e máscara vetorial. Originais não são regravados. Efeitos, smart objects e modos de mesclagem complexos precisam de conferência visual: biblioteca não prova equivalência ao Photoshop.

```
.venv/bin/python scripts/psd_cutouts.py inspect ORIGINAL.psd
.venv/bin/python scripts/psd_cutouts.py mask ORIGINAL.psd --layer 0 --mask MASCARA.png --out NOVA_VERSAO.psd
.venv/bin/python scripts/psd_cutouts.py png NOVA_VERSAO.psd --out DERIVADO.png
```

A máscara deve ter o canvas original. `--layer 0/2` seleciona uma camada dentro de um grupo. O PNG é derivado de renderização, nunca a única fonte editável. O pacote deve conservar as referências verificáveis ao PSD e às máscaras.

## Intercâmbio reutilizável

```
.venv/bin/python scripts/export_premiere.py ID \
  --snapshot SNAPSHOT_COMPILADO.json --av-sources FONTES_POR_CENA.json \
  --out Edit/ID/interchange/VERSAO_NOVA --lut GRADE.cube
```

O exportador novo é o padrão. O caminho anterior só roda com `--legacy` e conserva suas limitações; não usar para novas entregas. O pacote novo inclui PNGs em tamanho nativo, fontes A/V distintas por cena, links, coordenadas em pixels, MOGRTs da amostra aprovada, receita de importação e métricas. Não escreve no job nem no Premiere. Recusa falta de procedência de resolução/máscara, reserva incompatível e recursos de imagem não preparados pelo adaptador.

O snapshot exige `premiereCaptionPosition: [x, y]` explícito, em pixels. O estilo do job pode guardar esse campo para a compilação; não inferir coordenadas do 174/177.

A amostra `studio/templates/premiere/palavra-101-v1.mogrt` deriva da legenda aprovada no 177. Preservar a aprovação associada ao hash. Isso não fixa a posição de legenda de todos os vídeos: novas composições exigem configuração correspondente. MOGRTs são importados pelo passo de host; o XML não os incorpora como texto. Nunca substituir silenciosamente por PNG de palavras.

`package.json → hostPlan` registra limites e tarefas de conferência. Não marcar importação concluída pela mera geração do pacote. XML/MCP podem divergir: observar o resultado e corrigir somente o que faltou. Lotes geométricos têm no máximo 16 itens; resultados desconhecidos exigem inspeção antes de repetir. Áudio ausente na importação tem procedimento explícito; nunca duplicá-lo sem contagem/leitura prévia. O limitador do mix é conferido no host e no áudio exportado, não declarado aplicado por XML.

## Revisão visual automatizada

`studio.py review-scenes ID --plan PLANO.json --out NOVA_PASTA` produz referência, recomposição, sobreposição, diferença, alpha, detalhes de contatos e frames antes/depois de cada entrada/saída. Usa frame real com hash, imagens em coordenadas aprovadas, máscara separada opcional e camadas com `from/to`. Verifica canvas/transformação compartilhados entre base e frente. Veja teste executável em `tests/test_premiere_pipeline.py` para o contrato do plano.

O relatório mantém `approved: false`. Métricas de diferença não aprovam textura, recorte ou naturalidade. Corrigir apenas peças/regiões divergentes; depois registrar a decisão real de Lucas.

## Transferência e master externo

`studio.py premiere-handoff ID --project ARQUIVO.prproj --sequence ID_SEQUENCIA --package package.json --evidence EVIDENCIA.json`

Evidência: `userApproval`, `reviewer`, `notes`, hashes `projectSha256/packageSha256`, `sequenceId` e `checks` com `geometry`, `captions`, `avLinks`, `headHandles`, `tailHandles`, `saveReopen`, `mixLimiter` efetivamente conferidos. Não confundir autorização de transferência com aprovação final do master.

`studio.py premiere-candidate ID --master EXPORT.mov --project ARQUIVO.prproj --sequence ID_SEQUENCIA --dependencies DEPENDENCIAS.json --evidence EXPORTACAO.json`

Exportação: `exportedByPremiere`, `exportReceipt`, `outputSha256`, `projectSha256`, `sequenceId`, `durationFrames`. Inventário: `files: [{path, sha256}, ...]`. Requer handoff verificado, confere dependências e formato/decodificação completos. Não finge que o arquivo foi produzido pelo renderer.

`studio.py premiere-release ID --candidate REGISTRO.json --evidence APROVACAO_FINAL.json`

Aprovação final: `userApproval`, `reviewer`, `notes`, `outputSha256`, `candidateSha256`, `checks: visual/audio/completePlayback/noGuides/mixLimiter = passed`. Hashes do arquivo, projeto, dependências e evidências são reconferidos. Alteração invalida a liberação. Cópia para Prontos é verificada e não sobrescreve arquivo existente. O caminho antigo `render --master/release` permanece separado e protegido.

## Cache e desempenho

`pipeline_cache.py` mede hashing, probe, validação e construção. Cache usa conteúdo de entrada, receita, adaptador e binário; conferir hash de saída antes de reutilizar. Escrita incompleta nunca é hit. Não usar existência de arquivo como prova de validade. Locks impedem duas escritas no mesmo resultado; não apagar lock de outra execução por inferência.

Probe repetido é memoizado só durante a execução e invalidado por mudança de arquivo. Cópias de áudio usam nome pelo conteúdo, evitando colisões entre WAVs de mesmo nome. Ainda não há promessa de aceleração global: medir cada render e atacar o maior custo observado, preservando qualidade. Não reduzir resolução ou qualidade como otimização. Não apagar mídias editoriais nem resultados de acabamento como cache.

## Cintos e tênis: estado com/sem e máscara de contato

Correção explícita de 17/10: sobrepor a imagem com acessório à imagem sem, alinhar primeiro, mascarar a camada superior perto do objeto e aplicar feather amplo e bem esfumado na junção. Manter a base intacta. Recorte isolado no contorno do cinto/tênis não substitui esse método. Guardar ambos os estados e máscara recuperável; conferir cintura/barras em zoom e no frame anterior/posterior à entrada. Referência: ajuste feito por Lucas no cinto girl da cena 1 do 177, somente leitura. Detalhes em [layer-assembly](../skills/raquel-video-editor/references/layer-assembly.md).

Runtime PSD isolado: instalar com `uv pip install --python .venv/bin/python --target .runtime/psd-deps -r studio/psd-requirements.txt`. Pillow é fixado porque versões posteriores removem uma API usada pelo adaptador. Não atualizar sem rodar os testes de transparência e recuperação.

### Conferência mecânica da transferência

**Decisão de Lucas em 17/10/2026:** a validação de ponta a ponta das melhorias será realizada na próxima execução, no próximo vídeo. Não retomar esses testes no 177 finalizado. Na retomada do próximo vídeo, incluir essa pendência no plano: primeiro certificar a transferência com fixture em projeto separado; depois acompanhar o fluxo real até o master exportado pelo Premiere e a aprovação do arquivo exato. Conferir resolução e recuperação das máscaras, encaixes e estados progressivos, legendas, geometria, fontes por cena, vínculos e extensão/redução das margens A/V, limites do MCP, persistência após salvar/reabrir, limitador do mix e métricas de processamento/cache. Registrar evidências no novo vídeo; implementação e testes locais não equivalem à validação de ponta a ponta. A aprovação final continua dependendo da decisão real de Lucas vinculada ao hash do master.

`scripts/premiere_verification.py` compara leituras normalizadas antes de salvar e depois de reabrir: alvo projeto **e** sequência, identidade das mídias, quantidade, frames, fonte, geometria e vínculos. A leitura precisa incluir todas as páginas do MCP. Fonte de áudio ausente, clipe duplicado, coordenada diferente e alteração após reabrir reprovam a conferência. A legenda exige evidência renderizada além do texto. O verificador não aprova resultado editorial nem transforma uma resposta `ok` em playback realizado.

O teste real usa `scripts/premiere_transfer_fixture.py` e mídia sintética em `Edit/_editor/tests`. Nunca fazer testes de trim, importação ou salvamento em uma cópia de sequência dentro do vídeo pronto. Com edição simultânea do usuário, suspender mutações no Premiere até obter a janela de uso; continuar testes locais. A troca de projeto pelo MCP deve ser seguida de leitura real de projeto e sequência, pois a aba ativa pode permanecer em outro projeto.

### Otimizações preservando qualidade

O staging do renderer usa cópia independente por clone APFS quando disponível, com fallback para cópia normal. Não usa hardlinks: alterações na cópia e na origem não se propagam. O master deixa de ser decodificado duas vezes na mesma verificação; continua com uma decodificação completa obrigatória. Relatórios de render registram preparação/compilação, staging por arquivo, render e verificação. O cache de grade evita re-encode somente quando entrada, receita, adaptador/binário e hash da saída correspondem.

O campo opcional `premiereMediaId` no job permite usar PSD nativo no Premiere e manter `mediaId` como derivado PNG para a prévia do navegador. A compilação gera `premiereSrc`; tamanho/canvas de ambos devem corresponder ao mesmo registro. Não selecionar a camada PSD com limites diferentes sem compensar a geometria e rever. `cutoutProvenance` acompanha o pacote; originais, máscaras e inspeções são preservados em `recovery/` e constam de `dependencies.json`.

Após um handoff registrado, `pnpm validate:final ID` valida a liberação externa existente e seus hashes; não passa pelos gates antigos do renderer nem cria uma aprovação. Sem liberação do arquivo exato, falha.

### Correção do exportador PSD e do feather — 17/10/2026

Seguir a referência visual enviada por Lucas: faixa generosa de calça acima dos tênis, com bastante feather na borda recortada da máscara; tênis nítidos e base intacta. Não usar faixa mínima nem limitar a máscara pelo contorno da base. Detalhes em `layer-assembly.md`, seção de correção visual.

O adaptador agora grava PSD v1 conservador para uma camada raster normal de canvas integral, preservando pixels, nome, recursos de imagem e máscara separada. A contagem de camadas negativa identifica transparência do composto; o caminho anterior a tornava positiva ao reconstruir a árvore. O novo caminho grava canais sem compressão e não transfere descritores de camada obsoletos. Demais árvores mantêm o gravador existente com a sinalização corrigida. Testar recuperação de pixels/máscara, leitura independente e estrutura. Isso não equivale a abertura observada no Photoshop: manter `photoshopOpenVerified: false` até teste no aplicativo.
