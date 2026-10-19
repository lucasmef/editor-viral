# Recortes para entradas progressivas

Atualização de 15/10/2026: aplicar [fluxo vigente](../../../docs/FLUXO_EDICAO_PREMIERE.md). Antes de separar, conferir qualidade e apresentar o look completo apenas sem fundo sobre o vídeo. Aguardar aprovação explícita de Lucas para tamanho e localização; só então separar as peças usando esse gabarito. A recomposição deve reproduzir essa referência, não estimar posições independentes.

Atualização de 15/10/2026: ler obrigatoriamente [prompt validado de separação e registro de crops](separation-prompt.md). Um look por referência de geração, um item (peça ou grupo definido) por saída; preservação de pose, cor, textura e encaixe. No modelo one-shot, extrair primeiro no enquadramento/coordenadas da referência; crop ajustado pertence à preparação posterior para montagem, com offset registrado. Ler o [prompt one-shot aprovado](extraction-oneshot-lucas.md) e o procedimento para corrigir divergências em separation-prompt.md. O recorte fiel preserva o visível; reconstrução para entrada progressiva é uma base distinta identificada. Estas regras prevalecem sobre instruções genéricas de completar peças. Lucas fará as imagens da última cena do 174; não gerar novas tentativas nem alterar o Premiere nesta atualização.

Fluxo definido por Lucas em 14/10/2026. Aplicar depois do corte aprovado e do recebimento das imagens escolhidas.

## Checkpoint anterior à montagem

Preparar os recortes de **todas as cenas**. Entregar uma revisão organizada por cena com referência original, componentes separados e recomposição estática do look completo. Corrigir problemas e aguardar confirmação explícita dos recortes por Lucas antes de montar o vídeo com looks. Aprovação do corte ou escolha das imagens não aprova os recortes. A revisão look por look do vídeo não substitui este checkpoint.

## Sequência de aprovações

1. Apresentar as opções de takes de cada cena; Lucas escolhe.
2. Montar o vídeo completo com cortes mais justos; Lucas aprova esse corte.
3. Receber imagens escolhidas, conferir qualidade, sinalizar defeitos para decisão e apresentar o look completo apenas sem fundo sobre o vídeo, com guias, para Lucas aprovar tamanho e localização. Só após aprovação explícita executar recortes de todas as cenas sobre as coordenadas aprovadas.
4. Apresentar os recortes e suas recomposições; corrigir até Lucas aprovar.
5. A aprovação dos recortes libera a montagem e a continuidade das próximas etapas, sem perguntar novamente se pode montar. Preparar a prévia e aguardar o OK de transferência para Premiere. Continuam válidas as revisões posteriores e a aprovação da exportação exata.

Não confundir aprovação de takes, corte, imagens, recortes e exportação. Registrar a decisão em seu escopo real.

## Complementos gerados em contexto

Técnica confirmada por Lucas: cinto, calçado e outros complementos precisam encaixar na base existente, não ser fotografias genéricas isoladas. Cinto deve acompanhar a largura, curvatura e perspectiva da cintura, não aparecer enrolado ou aberto em uma orientação incompatível. Calçado deve respeitar a barra, o ângulo dos pés e as oclusões da calça.

Quando necessário, produzir um par registrado **base sem complemento / mesma base com complemento**. Partir da base e pedir somente a adição do complemento, preservando enquadramento, posição, escala, textura, cor, dobras e iluminação. Se a referência já tem o complemento, preservá-la como estado com complemento e gerar a versão sem ele, reconstruindo somente a área oculta. Manter origem, hashes e relação entre os dois estados.

Do estado com complemento, extrair apenas o complemento e a mínima região de contato indispensável. Sobrepor esse recorte à base sem complemento. Aplicar suavização localizada da máscara (feather) na junção quando necessária; preservar bordas nítidas de fivela, costuras, couro e sola. Isso não é um fade temporal do look inteiro. Não substituir toda a calça por uma nova geração para fazer aparecer um cinto ou tênis: diferenças involuntárias de textura e geometria provocam um salto.

Para tênis encaixados, seguir o [procedimento confirmado de alinhamento visual e feather](layer-assembly.md): calça sem tênis embaixo, calça + tênis acima; alinhar no olho primeiro, recortar a calça superior depois e aplicar feather amplo e bem esfumado somente na faixa inferior de junção. Conservar os tênis e uma faixa generosa de calça acima deles, como na referência visual de Lucas de 17/10/2026. Esse alinhamento visual é esperado entre dois estados gerados, diferente da duplicação idêntica da jaqueta. Conferir alinhamento sobrepondo os estados e alternando a visibilidade. Corrigir deslocamentos e diferenças nas regiões preservadas; não assumir que o pedido de “não mudar nada” foi obedecido perfeitamente. Preservar a máscara e a região de contato usadas. Registrar reconstruções ou discrepâncias residuais para revisão. O teste estático de encaixe faz parte da preparação dos recortes e não autoriza antecipar a montagem do vídeo.

## Planejar pela fala e pela referência

### Casacos com forro e camadas em sanduíche

Aplicar a [montagem por duplicação e máscara demonstrada por Lucas](layer-assembly.md). PSD pode permanecer como formato de trabalho; não converter nem gerar novamente por hábito. A completude da roupa interna depende do que aparece em cada estado do vídeo.

Para jaquetas, blazers e camisas abertas sobre outra peça, preparar uma imagem completa com o próprio verso/forro visível na abertura. Duplicar essa mesma imagem e extrair por máscara somente a frente (mangas, lapelas e painéis dianteiros). Nunca gerar frente e verso em chamadas independentes: textura, forma e posição precisam coincidir pixel a pixel. Preservar imagem completa, máscara e frente derivada, com hashes e a relação de derivação.

Ordem de composição: casaco completo atrás → parte necessária da blusa no meio → frente mascarada do mesmo casaco acima → acessórios conforme suas oclusões. Se a blusa só aparece sob o casaco, não exigir mangas ocultas; se aparecer sozinha, preparar uma versão completa para esse estado. Duplicar a instância da base já posicionada e substituir apenas pela fonte com máscara frontal, conservando canvas, origem, âncora, escala e posição. Se a base agrupa jaqueta + calça, retirar a calça apenas da máscara superior para não duplicá-la. A máscara da frente deve retirar também o forro atrás da gola quando necessário para a blusa entrar entre as camadas. Conferir o casaco sozinho antes da entrada da blusa e o conjunto depois, sem buracos na região do pescoço. Na cena 4 do 174, o jeans médio entra antes do amarelo: as jaquetas precisam funcionar completas já nesse primeiro estado.

### Acessórios independentes e coordenadas

Cada cinto, bolsa, óculos, corrente, boné, fone e calçado deve ter arquivo próprio e posição ajustável. Não juntar itens distintos em uma prancha PNG de produção mesmo que entrem ao mesmo tempo. Pares de calçados podem compartilhar um arquivo: Lucas confirmou que não é necessário separar pé esquerdo e direito. Se o par já estiver separado, pode continuar assim. Outros conjuntos exigem definição explícita do usuário. Preservar a relação de encaixe com cintura, gola e barra; mostrar a recomposição e os arquivos individuais na revisão. Uma prancha serve somente como contato visual, nunca como camada única para posicionar vários acessórios.

Usar um sistema de coordenadas comum por referência e registrar transformações/âncoras. Mudanças de cor involuntárias precisam ser confrontadas com a referência da própria cena; não corrigir por nome de cor apenas. Verificar o conjunto das quatro cenas, não somente a cena corrigida primeiro.

Antes de gerar, mapear para cada cena as peças que representam cada cor/conceito da fala, separadamente para girl e boy. Não agrupar apenas por proximidade na fotografia. Cada entrada independente deve ser uma camada; agrupamentos de peças exigem definição explícita de Lucas. A geração pode conter grupos contextuais definidos: jaqueta + calça para uma base simultânea, calça + tênis para extrair somente os tênis já em contato. Arquivo de geração não é necessariamente uma camada final. Não duplicar a calça inteira ao entrar o calçado; preservar uma única base e mascarar o complemento. Acessórios distintos permanecem separados mesmo com entrada simultânea. Jaqueta e blusa interna precisam das camadas em sanduíche descritas acima. Não agrupar os dois lados no mesmo arquivo de produção.

O recorte fiel mantém os limites visíveis da referência. Se uma peça precisa aparecer inteira antes de uma sobreposição, mapear uma base reconstruída separada para esse estado, sem modificar o recorte fiel nem sua borda de encaixe final. Não usar apenas o miolo visível como se fosse uma peça inteira; também não inventar uma nova barra no componente que precisa encaixar como na foto.

Quando o estado progressivo exigir reconstrução, limitar a edição à região oculta e identificá-la como reconstruída, mantendo pose, cor, material, textura e geometria visível. Registrar a relação com a referência e conferir estados isolado e composto. A regra antiga de completar peças indiscriminadamente foi substituída: seguir as exceções documentadas em separation-prompt.md. Não fingir que reconstrução é extração exata de pixels.

## Procedência obrigatória

Cada arquivo precisa de cena, lado, peça/grupo, etapa da fala, ID/hash da referência, caminho/hash de saída e versão. Nome sugerido: `cena-01-boy-camiseta-marinho-v02.png`. Usar a referência daquela cena como origem. Uma base derivada pode ser entrada no método contextual abaixo, desde que vinculada à mesma referência e identificada por hash. Nunca usar foto ou geração de outra cena por semelhança de cor. Conferir a imagem e o hash antes de cada chamada. Não mostrar nem cadastrar uma calça de outra cena como componente da cena 1.

Preservar originais e versões nas raízes externas. Registrar no job o mapa de componentes e o estado real: planejado, gerado, precisa-correção, pronto-para-revisão ou aprovado por decisão explícita. Só marcar o conjunto pronto quando todas as cenas estiverem cobertas; saída parcial deve declarar cenas/peças faltantes. Evidência da aprovação deve identificar manifesto e hashes exatos; alterar um recorte exige revisar o componente alterado.

## Conferência antes de apresentar

- Verificar procedência, geometria, cor/material, textura sem novos padrões e logomarcas; distinguir recorte visível de base reconstruída; inspecionar alpha, resíduos, halos e bordas sobre fundos claros e escuros.
- Reunir camadas em uma recomposição estática e comparar com a imagem escolhida: silhueta, ordem de sobreposição, encaixe de cintura/gola/mangas, escala relativa, posição dos acessórios. O look completo deve reproduzir a referência, não criar outro styling.
- Exibir por cena a referência, os componentes identificados, os estados progressivos e a recomposição. Não entregar uma sequência de imagens sem rótulos de cena.
- Registrar diferenças reais e corrigir antes de declarar pronto. Alpha existente não certifica recorte limpo; arquivos separados não certificam encaixe.

A posição e o tamanho do look no vídeo continuam ajustáveis depois. Mover ou escalar o grupo deve preservar as relações internas entre as peças; alteração do tamanho do quadro ou de um look não deve exigir recriar o styling.

## Exemplo confirmado: 174, cena 1

Jeans escuro: calça masculina em um arquivo; top inteiro + saia jeans femininos em outro grupo, conforme Lucas. Azul-marinho: camiseta masculina inteira independente e jaqueta feminina independente, encaixadas sobre a base existente. Burgundy: jaqueta masculina independente da camiseta e os acessórios correspondentes, conforme as entradas planejadas. As peças que permanecem usam os mesmos arquivos ao longo da cena.

Este exemplo pertence à cena 1 do 174. Mapear as outras cenas pelas respectivas imagens e falas, sem reaproveitar automaticamente peças, tons ou agrupamentos.

## Critérios de aceitação antes de apresentar

- Examinar resolução útil, textura e artefatos a 100% e no zoom previsto. Mostrar defeitos antes de investir nos recortes; aguardar decisão para a imagem afetada, continuando trabalho independente. Upscale não certifica qualidade.
- Registrar referência/hash, dimensões, limites de cada peça, âncoras e transformação do look completo. Sobrepor ou alternar referência/recomposição para conferir proporções, cor e posições.
- Jaquetas: verificar completa sem blusa, entrada da blusa e frente por cima. O forro deve existir no estado inicial; remover da frente apenas o necessário para a abertura, preservando gola/lapelas. Frente e completa derivam da mesma imagem, com máscara e registro comum. Rejeitar buracos, restos da blusa e gola mutilada antes da revisão.
- Arquivos de peças têm limites próprios com pequena folga útil para alpha/feather. Registrar o deslocamento ao aparar transparência e compensá-lo na montagem. Não embutir posição/escala da composição em PNG de tela inteira. Frente/completa DEVEM conservar o mesmo canvas/origem para substituição após duplicar a instância. Não aparar a frente de forma independente; o vazio inferior herdado da base com calça é necessário ao alinhamento. Isso não exige o canvas inteiro do vídeo.
- Reconstruções ocultas são declaradas; todos os estados de entrada devem funcionar, não apenas o look completo. Encaixes de cintura, gola, calçados e acessórios devem ser revistos em todas as cenas.

## Resolução e recuperação obrigatórias — 17/10/2026

Correção de Lucas após o 177: PNGs para o Premiere não podem ser reduzidos ao tamanho de exibição. Manter pixels nativos do PSD; escala é transformação da instância. Recorte não pode apagar pixels originais: preservar PSD com camadas/máscaras ou original + máscara independente. PNG alpha não recupera pixels removidos. Usar `cutoutProvenance` e `scripts/cutout_contract.py`; o exportador novo rejeita redução e ausência de fonte recuperável.

PSD é permitido diretamente quando o comportamento no Premiere estiver conferido; também pode ser preparado por código sem Photoshop manual. O adaptador `scripts/psd_cutouts.py` grava nova versão, preserva canais de pixels e máscara separada, atualiza o composto e verifica a reabertura. Não generalizar o suporte de RGB 8-bit raster para efeitos/smart objects/16-bit sem verificar.

Cinto/tênis: base sem objeto embaixo; estado com objeto sobreposto e alinhado; máscara superior próxima do objeto mantendo contato e feather amplo e bem esfumado localizado. Não isolar apenas o contorno nem substituir a roupa-base. Conferir estados antes/depois e detalhes da junção; ver `layer-assembly.md`.
