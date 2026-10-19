# Fluxo aprovado — preparação e ajustes finais no Premiere

> Estado operacional atualizado em 17/10/2026: [EDITOR_OPERACAO_ATUAL.md](EDITOR_OPERACAO_ATUAL.md). As descrições datadas abaixo preservam o histórico; capacidades atuais, comandos e limitações estão no índice vigente. Nenhuma atualização migra o 177.

Decisão de Lucas em 15/10/2026, após revisão da produção 174. Este documento consolida o método vigente e prevalece sobre as descrições anteriores de revisão no Remotion Studio e acabamento antes de aprovar o corte. Aprovação do fluxo não certifica implementação nem aprova resultados de mídia.

## Escopo e preservação

Remotion Studio sai da revisão e dos ajustes finais. Preservar o software, renderer, integrações, sessões e melhorias existentes: não desinstalar nem reconstruir por inferência. O harness continua útil para preparação e prévias. MCP configurado e testado por outro assessor; resultados e limites em [PREMIERE_MCP.md](PREMIERE_MCP.md). Lucas confirmou o fluxo: primeiro XML para a montagem inicial, depois MCP para ajustes no projeto importado. Não reinstalar a integração por inferência.

Preservar todos os ajustes, seleções, aprovações, arquivos e pacotes do 174. A atualização não reinicia o vídeo, não reprocessa acabamento, não regenera recortes, não reexporta XML nem substitui edições do Premiere. Referências históricas a “174 vazio” descrevem o reinício anterior, não o estado atual. Consultar o estado real ao retomar. Lucas tratará separadamente a questão da imagem defeituosa do 174; ela não é pendência nem bloqueio desta atualização de fluxo. A conferência geral de qualidade das imagens permanece nos próximos projetos.

## 1. Escolher tomadas

Examinar o bruto inteiro. ASR é índice, não escuta nem análise de expressão/gesto. Confrontar fala, erros conhecidos (burgundy, ousado, sofisticado), continuidade e tentativas incompletas.

Evoluir `scripts/takes_review.py` e `studio/templates/takes-review.html`, preservando o servidor oficial: **um player por cena**, todas as tomadas reproduzidas em sequência, botões abaixo para saltar para cada tomada, identificação do take atual e transcrição. Identificar limites entre tentativas e manter incompletas acessíveis. Navegação/reprodução não escolhe a tomada. Lucas seleciona uma por cena e confirma pelo fluxo oficial, mantendo IDs/hash do manifesto e origem dos intervalos. A mudança visual da galeria foi implementada em 15/10/2026 na preparação do 177; preserva o servidor e a confirmação separados da navegação.

## 2. Reservar margens, refinar e aprovar o corte

Após as escolhas, registrar uma janela útil com preferencialmente **1 segundo real antes e depois** de cada tomada. Usar 0,5 segundo quando houver menos contexto; registrar a disponibilidade efetiva, inclusive quando menor. Não incluir outra tentativa para completar a reserva.

Montar corte justo com waveform e conferência do áudio original, preservando palavras e respirações necessárias. Entregar vídeo completo para aprovação separada. O intervalo final é um subintervalo da janela: manter a reserva não significa exibi-la como pausa. Nunca substituir margem por freeze, repetição de frames ou silêncio artificial. Após reordenar cenas, revisar novamente cada junção e remapear eventos/legendas pela origem.

## 3. Acabamento após aprovação do corte

Processar maquiagem e cabelo nas janelas ampliadas depois da aprovação do corte. Fonte e intermediários: **2160×3840, 60 fps, ProRes 422 Standard, perfil 2**, Rec.709, PCM estéreo 48 kHz. Extrair do bruto 4K, sem upscale de acabamento menor; nunca HQ ou LT. Preservar máscaras, receitas e saídas de etapas. Operação e evidências em [finishing-handles](../skills/raquel-video-editor/references/finishing-handles.md).

Grading depois do acabamento, somente na gravação da Raquel/cenário. Preservar base tratada sem grading e receita/LUT/preset para ajustes; não alterar looks, textos ou inventar iluminação. A tradução para efeito nativo do Premiere requer calibração, não equivalência presumida.

**Voz neural:** o caminho legado permanece vinculado ao corte completo. `voice_windows.py` implementa fontes ampliadas por cena e reconformação por amostras; usar seu relatório e conferir hashes/reservas. Preservar ganho adicional zero. Aprovação do corte não aprova perceptivamente o acabamento.

## 4. Conferir qualidade das imagens antes de recortar

Examinar todas as referências escolhidas no tamanho original, a 100% e no tamanho/zoom previsto de uso. Verificar pixels úteis, nitidez, textura do tecido/jeans, artefatos, contornos, transparência, cor, deformações e partes ocultas a reconstruir. Registrar referência/hash e mostrar detalhes problemáticos.

Sinalizar qualidade insuficiente antes da separação trabalhosa. Lucas decide manter, corrigir ou substituir a imagem afetada; continuar tarefas independentes enquanto isso. Não regenerar por inferência nem tratar upscale como reparo certificado de textura. Incorporar essa conferência à revisão existente, sem criar microaprovações para detalhes técnicos normais.

## 5. Aprovar tamanho e localização antes de separar peças

Usar a imagem completa escolhida, sem fundo, como gabarito no vídeo. Lucas pode fornecer transparência pronta; caso contrário, preparar a remoção preservando a referência original. Posicionar girl/boy independentemente quando necessário, sem alterar suas proporções internas.

Registrar tamanho/posição do conjunto e as coordenadas locais da referência. Encaixar cada peça sobre esse gabarito, em vez de adivinhar posições. Mover/escalar o conjunto preserva as relações internas. Comparar recomposição e referência por sobreposição/alternância na mesma escala. Este é um checkpoint explícito anterior à separação: apresentar o look completo escolhido, apenas com o fundo removido, sobre o vídeo e com as guias visíveis. Lucas valida tamanho e localização. Corrigir essa prévia até a aprovação explícita; só então começar a separar ou reconstruir peças. Não antecipar recortes de componentes enquanto essa aprovação estiver pendente. Registrar a decisão vinculada à referência/hash e à transformação aprovada. Essa aprovação não aprova recortes ainda inexistentes.

Manter [padrão 101](PADRAO_VISUAL_101.md): segurança 6% por borda, guias de topo da roupa/barra da calça específicas do vídeo, excluindo acessórios de cabeça e calçados da medida. Não esticar saia/bermuda para alcançar a guia de calça. Conferir rosto, mãos e legenda. Prévias inclusive pequenas mostram guias; master não.

## 6. Recortar todas as cenas e aprovar

Somente depois da aprovação do tamanho e da localização do look completo, aplicar [contrato de recortes](../skills/raquel-video-editor/references/cutout-production.md). Preparar todas as cenas, não apenas a primeira, salvo exclusão explícita de Lucas. Atualização de 15/10/2026: Lucas fará os recortes da última cena do 174; não regenerar nem substituir essa cena por inferência. Para execuções futuras, ler o [prompt de separação validado](../skills/raquel-video-editor/references/separation-prompt.md): um look por referência, um item (peça ou grupo definido) por arquivo, nenhuma mudança de pose, cor, textura, perspectiva ou logomarca. Usar o modelo one-shot validado por Lucas: preservar enquadramento/coordenadas durante a extração, depois conferir e aparar vazio com offset para montagem. Grupos contextuais preservam contatos; não obrigar uma geração isolada por peça física. Tratar diferenças com correção localizada do item divergente, mantendo as saídas boas; ver tabela de diagnóstico no método. Aprovação visual não é prova de RGB idêntico. Conferir peça isolada, estados progressivos e recomposição sobre o gabarito, com origem cena/lado/peça/etapa/hash.

Jaquetas abertas: **completa com forro atrás → blusa necessária ao estado → frente mascarada da mesma jaqueta acima**. Ler a [demonstração com PSDs](../skills/raquel-video-editor/references/layer-assembly.md): duplicar a instância da base posicionada acima da blusa e substituir pela fonte frontal mascarada, mantendo canvas/origem/âncora e transformações. Não gerar frente e completa independentemente. Blusa sempre oculta pelo casaco não exige mangas; se aparecer sozinha, precisa de versão completa. Preservar gola/lapelas e conferir estados antes/depois da entrada. PSD pode ser mantido, sem conversão ou achatamento obrigatório.

Preservar o formato visível no recorte fiel, sem inventar barra nem alterar contatos. Se uma entrada progressiva precisar da peça inteira, produzir uma base reconstruída distinta, declarada e limitada às áreas ocultas, conferindo-a isolada e no encaixe final. Cintos/calçados encaixam na base por estados sem/com complemento. Para tênis encaixados, alinhar visualmente calça + tênis sobre a calça sem tênis antes de recortar; mascarar a calça superior com feather bem suave na junção inferior, conservando os tênis e a faixa mínima de contato. Preservar a calça-base. Acessórios distintos têm arquivos próprios; sapatos podem ser par se encaixarem, separados quando necessário.

Peças com dimensões próximas ao conteúdo, transparência real e pequena folga útil para bordas/feather. Não exportar cada peça em uma tela transparente do tamanho do vídeo. Guardar offsets/âncoras e compensar transparência aparada para manter posição. Para base/frente duplicadas, conservar obrigatoriamente o mesmo canvas e origem do asset, inclusive vazio inferior quando a base contém calça; não aparar a frente isoladamente. Isso é diferente de rasterizar no canvas da sequência inteira. Transformações de montagem devem ficar editáveis no Premiere.

Lucas aprova os recortes separadamente; corrigir problemas técnicos dentro da etapa. Aprovação dos recortes libera montagem/prévia, mas não substitui o OK de transferência ao Premiere nem aprovação da exportação.

## 7. Montar, revisar e transferir com OK

Preparar a montagem com entradas no gesto real/pompom, sons de clique sincronizados e ganhos registrados. Não iniciar looks antecipadamente por padrão. Entregar prévia para revisar conjunto, mantendo as guias.

Com o OK de Lucas, transferir a montagem inicial ao Premiere por XML; depois usar MCP para ajustes pontuais no projeto importado, respeitando as capacidades comprovadas. Não reconstruir toda a timeline pelo MCP nem reimportar XML sobre ajustes manuais por padrão. Organizar novas cenas sequencialmente; preservar a organização atual do 174 salvo solicitação. Sequências aninhadas por look são opção se permitem acesso às peças. Nos próximos projetos, entregar vídeo e voz separados por cena, sincronizados, já cortados na timeline e vinculados como par A/V para alongar ou encurtar juntos no Premiere. Cada arquivo de voz deve preservar a mesma janela de origem e as margens reais do vídeo; não entregar a voz inteira como única fonte nem apenas fatiar um WAV sem reservas. Manter SFX independentes. Validar vínculo e ajustes de entrada/saída na importação conforme o [contrato de XML](PREMIERE_XML.md#áudio-e-vídeo-por-cena-com-margens--decisão-de-lucas-15102026). Usar o exportador nativo e as janelas de voz descritos no índice operacional; validar a importação real. Gabaritos e guias não podem aparecer no master.

Registrar projeto/seqüência, versão de entrada, mídias/hashes, limitações e autorização do handoff. **Depois da passagem, o `.prproj` é a fonte da montagem.** O job externo mantém preparação, procedência e decisões; JSON/XML de entrada não são outra timeline a editar em paralelo. Ler o estado atual do Premiere antes de alterações, preservar edições pendentes e não reimportar uma versão antiga por cima dos ajustes de Lucas. Handoff não implementa sincronização bidirecional.

## 8. Texto editável e validação final

No próximo projeto, validar uma amostra da legenda no Premiere antes de aplicá-la ao vídeo inteiro. A conexão MCP e a exibição de texto no teste não aprovam o padrão 101 nem comprovam controle de fonte/contorno/brilho pelo MCP. Legendas devem ser texto editável. Testar legenda nativa e/ou gráfico/MOGRT com uma frase completa do padrão 101, incluindo fonte, cor, contorno, posição e halo final. Não adotar palavras PNG como solução definitiva; SRT sozinho não reproduz aparência. Verificar quais propriedades a integração realmente escreve e lê.

Manter palavra por palavra, omissões seletivas sem perder sentido/negação, continuidade entre palavras e cenas. Só o primeiro frame do vídeo inteiro fica sem legenda. A palavra final mantém aparência normal com brilho, sem aumento por inferência. Calibrar antes de aplicar em todos os vídeos.

Salvar, reabrir e exportar amostra verificando geometria, máscaras/crop, sobreposição, transparência, texto, frames, áudio e cor. Playback/escuta reais não podem ser substituídos por testes estruturais. Revisar e aprovar o arquivo final exato, com hash e evidências. Formato atual de entrega: ProRes 422 Standard, 1440×2560, 60 fps, Rec.709, PCM estéreo 48 kHz, salvo nova decisão.

## Estado de implementação

Consultar a matriz e os comandos em [EDITOR_OPERACAO_ATUAL.md](EDITOR_OPERACAO_ATUAL.md). A galeria contínua e a voz por janelas foram implementadas em 16/10. A atualização de 17/10 adiciona exportação nativa, contratos de máscaras/resolução, revisão por cena, métricas e candidato/release externo. A validação no host é evidência separada: não declarar capacidades verificadas apenas porque o comando existe.

## Reprodução contínua das tomadas — correção de 16/10/2026

Um play reproduz todas as tomadas da mesma cena até o fim, incluindo interrompidas, em um único vídeo e uma única barra de tempo. Não depender da troca de arquivos no evento `ended`. Mostrar a tomada atual e sua transcrição conforme o tempo do player; os botões de salto apenas navegam. “Escolher tomada em reprodução” e os seletores individuais marcam a preferência sem parar o vídeo; “Confirmar escolhas” registra a decisão separadamente. Reprodução nunca seleciona automaticamente.

`scripts/takes_review.py build` prepara esse formato para novas galerias. Para atualizar uma galeria existente, usar `continuous ID --directory DIRETORIO`: preserva `manifest.json`, IDs, intervalos e hash das escolhas; adiciona vídeos por cena e `playback.json`, guardando o HTML anterior. Esta operação não altera a timeline nem aprova cortes. O servidor oficial permanece responsável pela confirmação.


### Galeria compacta — 16/10/2026

Uma cena por aba, vídeo grande limitado à altura disponível e painel lateral compacto com todos os botões de tomadas visíveis, sem carrossel horizontal. Play de todas as tomadas e escolha atual são controles pequenos e separados. O servidor suporta HTTP Range para saltos em vídeos ainda não baixados por inteiro; o salto aguarda metadados e entra 40 ms depois do limite para evitar arredondamento na identificação da tomada. Trocar de cena pausa a reprodução anterior. Escolhas explícitas feitas no chat podem ser registradas parcialmente, vinculadas ao mesmo hash do manifesto; não aprovam o corte. Na retomada, preservar escolhas locais ainda não confirmadas e carregar as decisões já registradas.
