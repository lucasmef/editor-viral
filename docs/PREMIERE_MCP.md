# Integração local Premiere MCP — 15/10/2026

> Estado operacional atualizado em 17/10/2026: [EDITOR_OPERACAO_ATUAL.md](EDITOR_OPERACAO_ATUAL.md). As descrições datadas abaixo preservam o histórico; capacidades atuais, comandos e limitações estão no índice vigente. Nenhuma atualização migra o 177.

## Correção validada: movimento entre faixas (15/10/2026)

**Estado vigente: premiere-pro-mcp 1.24.0 + patch local `safe-move-v1`.** Esta seção substitui a proibição geral de movimento entre faixas nos relatos anteriores. O pacote, a origem, o conector e a configuração continuam os mesmos; não foi criado outro MCP. Código e aplicação reversível documentados em [patch local](../integrations/premiere-mcp/patches/README.md).

O handler agora confere destino e percurso antes de escrever; usa uma faixa livre existente quando necessário; compara todos os clipes A/V e seus valores legíveis após cada passo. Destino ocupado ou falta de trajeto retorna recusa sem mutação. Não cria faixa automaticamente. Clipes vinculados ou animados e trajetos com transições são recusados por ainda não terem preservação validada. Falha após escrita retorna estado não verificado e exige inspeção, sem alegar rollback.

**Prova no host 26.5.2:** o caso que antes apagava o PNG original passou usando V7 intermediária. Também passaram movimentos de ida e volta do PNG com ajuste manual de escala 93%, vídeo cortado, MOGRT com texto/fonte/cor e áudio com volume. Onze comparações de IDs, tempos, faixas e componentes de todos os dez clipes passaram; colisão no destino foi recusada sem alterações. Após salvar, fechar e reabrir, a montagem e as propriedades conferem com o baseline. A faixa V7 fica vazia no teste.

**Prova de saída:** `exports/validacao-move-corrigido.mp4` tem 479 frames a 60 fps. Todos os 479 frames decodificados são idênticos aos de `validacao-v3.mp4`; o áudio PCM decodificado também é idêntico. Isso inclui a aparência das legendas existentes. A garantia é sobre esses testes, não sobre quaisquer máscaras/keyframes/dados que o CEP não enumere.

Projeto: `/Users/lucas/Movies/Vídeos/Edit/_editor/tests/premiere-mcp-1.24.0-20261015/validacao.prproj`. Backup anterior: `validacao-antes-correcao-move.prproj`. Evidências: `evidence/move-corrigido/`. O 174 permaneceu fechado, SHA-256 `433b015bce3a15d120635822774782b1bb9dc20b5e836927e0af5827d2dfeebd` e mtime `1792067558.5755324` inalterados.

Validação de software: 10 testes do patch e 160 testes do harness passaram; `pnpm check` passou. `pnpm status` apenas consultado; `pnpm validate:final` permanece bloqueado pelos checkpoints, como esperado. Nenhuma produção foi exportada. Recarregar uma conexão Codex já em execução para receber o patch; os testes stdio já usaram o código corrigido. Reinstalação/atualização não deve reaplicar esse patch cegamente: o instalador local confere o código original exato.


## Atualização final: duplicação, corte e texto editável (15/10/2026)

Esta seção prevalece sobre os resultados históricos abaixo. Integração continua **premiere-pro-mcp 1.24.0**, original, sem patch de código, sem outro servidor MCP e sem alteração de segurança. O 174 permaneceu fechado e seu SHA-256 permaneceu `433b015bce3a15d120635822774782b1bb9dc20b5e836927e0af5827d2dfeebd`, mtime `1792067558.5755324`.

### Entrega atual

- Projeto: `/Users/lucas/Movies/Vídeos/Edit/_editor/tests/premiere-mcp-1.24.0-20261015/validacao.prproj`.
- Amostra final: `exports/validacao-v3.mp4`, **479 frames, 720×1280, 60 fps, 7,983333 s**, H.264/AAC estéreo 48 kHz, 16.637.361 bytes. SHA-256 `06426526a6b03147702352339074dc56de3b4b470c8f199a60be285bb81938d4`.
- Evidências: `evidence/capacidades-v3/`, incluindo leituras MCP, frames, áudio decodificado, medições e este relatório.
- `validacao-antes-v2.prproj` preserva o teste anterior. `diagnostico-movimento-entre-faixas.prproj` registra uma falha encontrada e **não é a amostra final**.
- MOGRT permanente: `templates/Sports Graphic Overlay.mogrt`, modelo que acompanha o Premiere da Adobe. Dependência gerada pelo Premiere em `Motion Graphics Template Media/b9f09325-ee14-4fc6-9f60-0883f454d0af/Sports Graphic Overlay.aegraphic`, junto do projeto. Preservar ambas as pastas.

### O que passou no host e na exportação

| Operação | Evidência e limite |
|---|---|
| Duplicar vídeo | `duplicate_clip` copiou base de 4 s para V5; movimento dentro de V5 para 4 s preservou todos os cinco clipes originais. |
| Aparar vídeo por um frame | `trim_clip` mudou Out da cópia de 4 s para 239/60 s, reduzindo a cópia para 239 frames. Foi necessário fornecer ffprobe real no PATH. |
| Dividir vídeo | `split_clip` em V5 no frame 361, 6,0166667 s, produziu limites adjacentes corretos; frames exportados 360 e 361 mostram fonte 120 e 121, sem salto. Usa QE não documentado; redistribuição de keyframes não validada. |
| Duplicar PNG | Cópia com mesmo in/duração, originalmente em defaults de Motion. `copy_effect_values` copiou 11 propriedades de Motion, inclusive escala manual 93% e rotação 7°; `copy_effects_between_clips` copiou Crop e valores. A cópia recebeu posição independente 540×330 e início frame 31. Original continua 340×600, início frame 30. |
| Repetir áudio | `duplicate_clip` direto de WAV permanece limitado. Alternativa comprovada: `overwrite_clip` do mesmo item em A2 no frame 301, seguido de `copy_effect_values` de Volume. O áudio original não mudou. |
| Texto editável pelo MCP | `import_mogrt` do modelo Adobe Sports Graphic Overlay com Title “texto via MCP”; depois `get_mogrt_component` e `set_effect_property`, efeito Graphic Parameters, Title alterado para “texto alterado”, fonte ArialMT, tamanho 48. Texto renderizado e persistente após reabrir. Não é PNG. |
| Aparência do MOGRT | Highlight Color alterada para ARGB [1,30,160,240], lida corretamente; Motion escala 37,5%, posição final 500×1050. Frames finais mostram o texto inteiro em uma faixa clara com detalhe azul. É demonstração técnica, não padrão 101 aprovado. |
| Persistência | Salvar, fechar e reabrir funcionaram; IDs/ranges originais e escala 93% preservados. Modelo e mídia resolvidos localmente. |

Áudio decodificado: sinal original 1–1,5 s e repetição 5,0166667–5,5166667 s, ambos pico 3008/32768 e RMS aproximadamente −24,01 dBFS; silêncio nos intervalos 0–0,9, 1,6–5 e 5,6–7,9 s. PCM extraído das exportações v2 e v3 é idêntico. Isso é medição, não escuta crítica. Frames inspecionados da v3: 30, 31, 90, 300, 360, 361 e 478; confirmam entrada da cópia no frame 31, transparência, rotação, sobreposição, texto alterado e continuidade na divisão. Sem aprovação estética do usuário nem playback completo alegado.

### Falha concreta: mover entre faixas

`move_clip` com `new_track_index` pode substituir um clipe na faixa de destino **na posição antiga da cópia**, antes de mover ao tempo final, e mesmo assim responder verified. Neste teste, mover a cópia da base de V5 em 0 s para V1 em 4 s removeu o original em V1; mover a cópia PNG de V5 em 0,5 s para V2 em 4,5 s removeu o original em V2. A próxima leitura detectou as ausências.

Recuperação: estado problemático salvo em projeto de diagnóstico; fechado; reaberto o teste original salvo anteriormente. As operações foram refeitas com movimentos na mesma faixa e conferência dos cinco IDs/ranges originais após cada etapa. **Não usar movimento entre faixas em produção com esta versão sem corrigir e testar esse comportamento.** A guarda de projeto e o verified do clipe movido não garantem preservação do resto da sequência.

### Dependência corrigida e reconexão

Adicionado isoladamente `@ffprobe-installer/darwin-arm64` **5.0.1**, do registro npm, licença declarada LGPL-2.1; o binário informa **ffprobe n4.4.1**, Apple Silicon. Download com SHA-512 conferido contra `dist.integrity`: `sha512-vwNCNjokH8hfkbl6m95zICHwkSzhEvDC3GVBcUp5HX8+4wsX10SP3B+bGur7XUzTIZ4cQpgJmEIAx6TUwRepMg==`. Nenhuma dependência existente foi reinstalada.

Local: `.runtime/ffprobe-darwin-arm64-5.0.1/package/ffprobe`. Acrescentado PATH somente em `[mcp_servers.premiere_pro.env]` no Codex:

```toml
PATH = "/Users/lucas/Documents/Codex/editor/.runtime/ffprobe-darwin-arm64-5.0.1/package:/Users/lucas/Documents/Codex/editor/.local-bin:/Users/lucas/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
```

Recarregar a conexão MCP para receber esse ambiente; abrir o Premiere e verificar a conexão, o projeto e a sequência antes de editar. Os testes desta conversa usaram cliente MCP stdio local com esse PATH e guarda `expected_project_path`, não uma implementação alternativa do servidor. Nenhuma mídia enviada a serviços externos; nenhuma fila global de exportação iniciada.

### Texto: alcance real e recomendação

Há 73 modelos Adobe locais: 60 Premiere e 13 After Effects. O modelo After Effects testado funciona no Premiere sem instalar o aplicativo After Effects. Ele expõe Title, fonte, tamanho, três cores e dois controles de alinhamento. Foram efetivamente escritos texto, fonte, tamanho e Highlight Color; alinhamentos apenas enumerados. Posição/escala da peça inteira foram escritas via Motion. Não expõe stroke/contorno nem glow/brilho; não alegar suporte a essas propriedades com esse modelo.

Para padrão 101 e brilho da palavra final, preparar um MOGRT específico que publique os controles necessários e calibrar uma amostra. A autoria/alteração desse modelo pode exigir After Effects e intervenção manual. Títulos nativos criados no Premiere continuam editáveis pela interface, mas seu Source Text não está disponível nesse caminho MCP. Legendas SRT nativas continuam sem leitura/escrita completa de estilo por esse CEP. Importar SRT não valida fonte, contorno ou halo.

Recomendação: **manter este MCP**, usar composição de chamadas existentes para duplicar mídia e copiar ajustes, e complementar somente o modelo de legenda e, se necessário, a correção pontual de movimento entre faixas. Não foi desenvolvido novo MCP. Não migrar o 174 nesta tarefa. Não extrapolar a cópia de efeitos estáticos testada para máscaras, keyframes, retiming ou qualquer efeito arbitrário.

---

## Histórico das validações anteriores


## Atualização: conexão e amostra comprovadas

Esta seção substitui o estado pendente descrito no levantamento inicial abaixo. Lucas autorizou salvar e fechar o projeto aberto. O `174-validacao-XML.prproj` foi salvo pela interface (asterisco desapareceu; arquivo atualizado às 09:32:38 de 15/10/2026) e fechado. O Premiere foi reiniciado. Nenhuma edição da montagem do 174 foi feita.

O conector assinado iniciou automaticamente, inclusive seu componente headless. `verify_premiere_connection` retornou **overall ready**, com servidor, conector, projeto e sequência confirmados. Foi usado o servidor original instalado, via cliente MCP stdio local de diagnóstico; as ferramentas ainda não foram expostas nativamente nesta conversa já aberta. A entrada persistente do Codex continua configurada.

Projeto: `/Users/lucas/Movies/Vídeos/Edit/_editor/tests/premiere-mcp-1.24.0-20261015/validacao.prproj`.
Exportação: `exports/validacao-v1.mp4`, no mesmo diretório. Modelos preservados em `templates/`, mídia em `media/` e evidências em `evidence/`. O projeto de teste foi salvo, fechado e reaberto pelo MCP. O 174 permaneceu fechado.

### Resultados efetivamente observados

| Teste | Resultado |
|---|---|
| Leitura de projeto, sequência, faixas, clipes, IDs, tempos e arquivos importados | Funcionou no teste, inclusive após reabertura |
| Importação de vídeo, WAV e dois PNGs próprios | Funcionou; PNGs 320×480 e 240×160, sem canvas da sequência |
| Sequência | 720×1280, 60 fps, timebase 4233600000 ticks/frame, áudio 48 kHz estéreo |
| Colocação de clipes | `overwrite_clip` funcionou em faixas separadas; insert com ripple e reordenação de cenas não foram testados |
| Movimento de um frame | PNG B movido de 1 s para 61/60 s; leitura e frames exportados confirmam entrada no frame 61 |
| Duração de PNG | `set_clip_duration` ampliou A para 2,5 s e B para 2 s; saídas confirmadas nos frames 180 e 181 |
| Trim pela origem | `trim_clip` recusou PNG por falta de duração finita/ffprobe; operação inadequada para prolongar still. Trim de vídeo ainda não validado; ffprobe ausente |
| Duplicação de áudio | `duplicate_clip` recusou porque não conseguiu ler marks restauráveis; nenhuma cópia criada. Não declarar duplicação genérica validada |
| Posição, escala, rotação, opacidade | Escrita e leitura funcionaram. A: posição final 340×600, escala 93%, rotação 7°. B: 390×650, opacidade 75% |
| Ajuste manual preservado | Escala A alterada pela interface de 90% para 93%; depois MCP alterou apenas posição. Escala 93% e rotação 7° permaneceram, inclusive após salvar/fechar/reabrir |
| Crop | Efeito Crop separado adicionado via QE; Left 10 e feather 2 lidos depois da reabertura. Não confundir com Crop nativo de Motion, que continuou zero. O corte de 10% fica dentro da margem transparente desta fixture; a amostra não prova visualmente a borda de crop sobre pixels opacos |
| Máscaras | Nenhuma máscara arbitrária criada/editada; permanece limite não validado |
| Áudio | WAV colocado de 1 a 1,5 s e ganho −6 dB. Leitura após reabertura: −5,9999997 dB. Export decodificado tem sinal nesse intervalo e silêncio nos intervalos 0–0,9 e 1,6–4 s; pico 3008/32768. Medição, não escuta crítica |
| Texto gráfico | Modelo Adobe Basic Title gerado pelo helper existente do pacote com “texto editável”, importado como Graphic/Text. Texto visível na interface e na exportação, sem PNG de palavras |
| Legenda nativa | SRT importado; criação aceitou, mas MCP não conseguiu contar/ler tracks. Interface mostrou Subtitle e export exibiu os dois cues. Aparência padrão apenas, sem aprovação do padrão 101 |
| Exportação | Premiere produziu MP4 H.264 Main, 720×1280, 60 fps, Rec.709, 4 s, AAC estéreo 48 kHz; 8.381.689 bytes. Export direto da sequência, nenhuma fila global iniciada |

Frames exportados inspecionados: 29, 30, 60, 61, 90, 179, 180, 181 e 210. Confirmados transparência fora das peças, sobreposição semitransparente, peça A rotacionada, texto gráfico central e legenda nativa inferior, além dos limites temporais. Os dois textos são intencionais para comparar mecanismos, não uma proposta estética. Não houve playback audiovisual completo nem avaliação do halo/fonte/contorno do padrão 101.

### Limitações novas demonstradas

1. O helper `bakePremiereTitle` gera `definition.json` com BOM, mas `import_mogrt` 1.24.0 rejeita esse BOM. Preservados o original e uma variante com somente o BOM inicial removido; a variante importou. Nenhum código do servidor foi alterado.
2. `get_mogrt_component` confirmou que o título Premiere tem Opacity, Motion, Vector Motion e Text, mas **não expõe Source Text para leitura/escrita por esse MCP**. A edição posterior do texto exige interface ou modelo After Effects com controles publicados. Não há prova de controle MCP de fonte, contorno ou glow nesse título.
3. `read_sequence_captions` retornou `captionReadSupported:false`, apesar das legendas presentes e renderizadas. Não usar retorno vazio como ausência de legendas.
4. Falhas de trim e duplicação bloquearam mutações posteriores. Foram inspecionados IDs e ranges atuais e reconhecida a revisão de recuperação pelo mecanismo próprio antes de prosseguir; nenhuma falha foi repetida cegamente.

Recomendação: usar esta solução para leitura e alterações pontuais já comprovadas, com guarda de projeto e releitura após cada mudança. Ainda não aprovar migração integral do 174. Complementos candidatos devem ser restritos a texto/estilo exposto em MOGRT, normalização de BOM e diagnóstico de duplicação/trim, depois dos testes específicos. Segurança de ajuste manual foi comprovada para escala preservada durante alteração de posição, não para qualquer operação arbitrária.

## Estado observado

Instalado `premiere-pro-mcp` **1.24.0**, origem https://github.com/leancoderkavy/premiere-pro-mcp, licença MIT. Release `v1.24.0`, publicada em 12/10/2026, não prerelease. Pacote do registro npm com nome exato; não é `adobe-premiere-pro-mcp`. SHA-512 do tarball conferiu com `dist.integrity` do registro. Isso confere integridade do download, não é uma auditoria completa de segurança.

Premiere instalado: **26.5.2**. Node existente: **24.19.0**, atende ao requisito >=20.19.0. Dependências do MCP isoladas em `.runtime/premiere-pro-mcp-1.24.0/package`, com lockfile próprio. Não foi criado outro servidor MCP.

Conector `MCPBridgeCEP.zxp` da mesma release instalado com sucesso pelo **UnifiedPluginInstallerAgent da Adobe** em `/Library/Application Support/Adobe/CEP/extensions/MCP for Adobe Premiere Pro`. O pacote contém assinatura em `META-INF/signatures.xml`; foi aceito pelo instalador Adobe. Não foi executado `--install-cep`: esse script habilita `PlayerDebugMode` em CSXS 8–14. Nenhuma alteração de segurança foi aplicada nesta tarefa.

Codex: entrada global `mcp_servers.premiere_pro`, stdio, executável `/Users/lucas/.local/bin/node`, argumento `/Users/lucas/Documents/Codex/editor/.runtime/premiere-pro-mcp-1.24.0/package/dist/index.js`. `POSTHOG_API_KEY` vazio desativa a telemetria desse pacote. Os demais MCPs foram preservados. Sem endpoint público e sem envio de mídia.

## Evidência e bloqueio atual

- Inicialização MCP real via stdio passou, identificando nome e versão; `tools/list` retornou **432 ferramentas**. O diagnóstico usou negociação legada 2025-11-25; a configuração Codex mantém modo automático. Isso não prova descoberta nesta conversa já aberta.
- `verify_premiere_connection` respondeu `MCP_SERVER_CONNECTED`, mas `PREMIERE_CONNECTOR_UNREACHABLE`. Projeto e sequência não foram verificados pelo MCP.
- Interface observada: `174-validacao-XML.prproj *`, com alterações não salvas. Não foi salvo, fechado ou modificado pelo assistente.
- Depois da instalação, Window > Extensions ainda não apresentou o conector. Reinício seguro do Premiere é necessário antes de continuar. Lucas foi solicitado a salvar seu trabalho e reiniciar. Não há autorização inferida para descartar alterações.
- **Projeto de teste Premiere e exportação ainda não produzidos. Nenhuma operação editorial está validada no host.**

## Iniciar e reconectar

1. Salvar o trabalho aberto por decisão do usuário; reiniciar o Premiere quando seguro.
2. Abrir Window > Extensions > MCP for Adobe Premiere Pro e conferir Running. Não reinstalar nem habilitar debug apenas porque o diagnóstico não reconhece o diretório do instalador Adobe.
3. Recarregar a conexão `premiere_pro` no Codex (se necessário, reiniciar o Codex após preservar o trabalho). O servidor inicia sob demanda pelo cliente; não executar um servidor HTTP.
4. Executar `verify_premiere_connection` antes de editar. CEP usa a pasta temporária local `premiere-mcp-bridge`; o servidor e o painel devem concordar sobre o caminho. Essa pasta é transporte, não armazenamento de mídia ou modelos.
5. Em testes e alterações futuras, ler projeto/sequência/IDs atuais e enviar `expected_project_path` com o caminho absoluto do projeto de teste em cada ferramenta CEP. Não aplicar índices antigos depois de mudanças manuais. Não regenerar a montagem inteira por cima de ajustes no Premiere.

## Capacidades inspecionadas, ainda não testadas no Premiere

| Requisito | Implementação encontrada / limite | Validação no host |
|---|---|---|
| Ler projeto, sequência, faixas, clipes e posições | Ferramentas de leitura e snapshots disponíveis; solicitar caminhos quando necessários | Pendente |
| Importar vídeo, áudio e PNG próprio | Importação e colocação de mídia disponíveis; usar RGBA nas dimensões próprias | Pendente |
| Inserir, mover, aparar, duplicar, ordenar a 60 fps | Ferramentas de timeline com verificações de grade; a release inclui correção de marks no 26.5.2 | Pendente; medir ticks e frames |
| Posição, escala, rotação, opacidade | Motion e propriedades de efeitos; descobrir nomes/índices antes de escrever | Pendente |
| Crop | `crop_clip` altera/lê valores; inclusão inicial usa catálogo QE legado | Pendente |
| Máscaras | `compute_mask_fit_motion` apenas calcula geometria a partir de efeito existente; não cria máscara. UXP possui auditoria de presença de Object Mask, não edição de contornos/tracking | Criação/edição arbitrária não comprovada |
| Volume e SFX | Ferramentas de áudio e colocação em timeline disponíveis | Pendente |
| Ajustes manuais preservados | Escritas pontuais e guarda de projeto ajudam, mas não bastam como prova | Pendente antes/depois e reabertura |

## Texto editável

`create_caption_track` importa legenda e verifica estrutura, não aparência. `read_sequence_captions` diagnostica a capacidade do host; CEP frequentemente não enumera as legendas. `get_caption_style_guidance` **não altera** fonte, contorno, sombra ou posição: produz instruções para Properties/Track Style. Brilho final e aparência não estão validados por SRT.

`import_mogrt` aceita valores de texto e lê o resultado em controles expostos. `get_mogrt_component` permite inspecioná-los. Modelos de After Effects podem expor texto e propriedades; fonte, contorno, posição e brilho dependem dos controles realmente publicados no modelo e precisam de teste. Propriedades não expostas exigem editar o modelo ou intervenção manual. Não presumir After Effects instalado.

`add_title` distingue modelos Premiere e After Effects: para títulos Premiere, grava o texto em uma cópia do template antes da importação, pois não há texto gravável exposto naquele caminho; isso não é editar arbitrariamente um título já existente. A descrição informa retenção de somente 50 cópias geradas em Application Support. **Não usar essa retenção como dependência de produção:** preservar o MOGRT definitivo sob a raiz oficial Assets e importar essa cópia. Texto continua gráfico editável no Premiere, sujeito à confirmação no host; nunca converter palavras em PNG para cumprir este requisito.

## Próxima validação autorizada

Criar projeto separado sob Edit/_editor/tests/premiere-mcp-1.24.0-20261015; mídia sintética, sem usar ou alterar o 174. Sequência 60 fps com vídeo, dois PNGs RGBA de dimensões distintas, texto gráfico editável e áudio. Registrar IDs, posições, in/out, parâmetros e hashes; testar uma alteração manual e depois uma escrita MCP em outra propriedade. Salvar apenas o teste, reabrir com segurança, exportar somente essa sequência diretamente com preset explícito, sem iniciar fila AME global. Conferir frames de entrada/saída, alpha/sobreposição/geometria, texto e áudio decodificados. Não chamar exportação enfileirada de concluída nem checagem de dados de aprovação visual/sonora.

Recomendação provisória: continuar avaliando a solução existente. Não há evidência que justifique um novo MCP. Eventuais complementos devem focar somente lacunas demonstradas, especialmente estilo de legendas e máscaras.

## Ocorrência de dependências

A primeira chamada de pnpm no subdiretório detectou a raiz do editor e removeu três vínculos de desenvolvimento. A revisão automática recusou uma instalação ampla de restauração por risco de reinstalar dependências. Os arquivos originais permaneciam em node_modules/.pnpm; foram restaurados apenas os vínculos typescript, @types/react, @types/react-dom e tsc, e o indicador devDependencies. `pnpm check` passou. A instalação efetiva do MCP usou `--ignore-workspace --prod --ignore-scripts`. Nenhuma versão de dependência do editor foi atualizada.

Fontes: [repositório](https://github.com/leancoderkavy/premiere-pro-mcp), [release exata](https://github.com/leancoderkavy/premiere-pro-mcp/releases/tag/v1.24.0), [MCP no Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), pacote local 1.24.0 e observações registradas nesta sessão.

## Evidência operacional de 17/10/2026

A abertura de um projeto XML de teste retornou sucesso, porém a sequência ativa lida em seguida era de outro projeto durante uso simultâneo. Portanto, `expected_project_path` é necessário mas não suficiente: confirmar também a sequência alvo e a identidade dos clipes antes de qualquer mutação. Não executar testes enquanto Lucas trabalha no projeto protegido. Estado e pendência da validação da nova versão: [relatório](audits/EDITOR_MELHORIAS_2026-10-17.md).
