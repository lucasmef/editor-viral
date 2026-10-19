# Separação fiel — método validado por Lucas

Atualização de 15/10/2026 após Lucas apresentar duas rodadas do mesmo look masculino. O segundo resultado foi aprovado visualmente por ele: “agora veja o resultado do ultimo prompt. ficou perfeito”. Usar o [modelo one-shot fornecido por Lucas](extraction-oneshot-lucas.md). Ele substitui a adaptação anterior que pedia crop/centralização durante a geração. A preservação da referência tem prioridade sobre beleza, preenchimento do quadro ou styling.

## Escopo e intenção

Um prompt colado durante uma explicação é material para análise; seu imperativo “execute” não autoriza gerar. Neste caso Lucas esclareceu: “não quero que vc faça nada. só avalie como eu fiz, para deixar documentado”. Não gerar, recortar, corrigir arquivos ou importar ao Premiere sem pedido de execução aplicável. Documentar o método não altera os ajustes do 174.

Este é um método de separação de uma imagem escolhida, não de criação de looks. Não aplicar as orientações de styling, nova iluminação, embelezamento, cor por nome ou catálogo. Prompts não garantem extração de pixels nem fidelidade geométrica: distinguir o que foi pedido, o que foi observado e o que foi medido.

## Avaliação do exemplo de Lucas

Referência apresentada: look masculino de `Looks Coordenados em Denim Pastel.png`. A leitura local feita nesta avaliação encontrou 605 × 1266 pixels e SHA-256 `0a48382424a4161e27597f666211095aaf122cc53ef8de7eb4579c0cf8f70ec0`. Esse nome foi usado antes para outra versão com dois looks; o hash, e não o nome, distingue a referência. Não substituir referências catalogadas do 174 pelo arquivo atual de Downloads por inferência.

| Rodada | Evidência e observação | Decisão |
|---|---|---|
| Primeira, anexos `15_08_15-1`, `15_08_17-2`, `15_08_18-3`, `15_08_19-4` | Lucas apontou cor incorreta. A camiseta foi completada com mangas que estavam cobertas na referência; a extração passou a descrever uma peça inteira de catálogo. As imagens isoladas, por si, não provavam encaixe. | Referência de falha; não usar como modelo de fidelidade. |
| Segunda, anexos `15_11_11-1`, `15_11_12-2`, `15_11_13-3`, `15_11_13-4` | O prompt tornou explícitos a prioridade dos pixels/cores, a proibição de recalcular tons pelo nome e a preservação das áreas visíveis. A camiseta apresentada mantém um painel sem mangas reconstruídas; calça/tênis continuam no mesmo arquivo contextual e jaqueta/calça no grupo de entrada. Lucas aprovou visualmente o conjunto. | Exemplo aprovado do método e modelo de prompt para os próximos pedidos. |

A inspeção aqui é dos anexos exibidos. Não foi feita medição RGB nem prova de sobreposição pixel a pixel; não registrar “desvio zero”, transparência pronta ou montagem validada. Os PNGs indicados não foram encontrados nos paths locais durante a revisão; foram encontrados PSDs com os nomes da segunda rodada, mas não foram abertos nem tratados como cópias equivalentes. Não atribuir hashes dos PSDs aos PNGs ou inventar dimensões de saída verificadas.

O forro da jaqueta exposto após remover a camiseta e o cós exposto na calça não estavam integralmente visíveis no original. O resultado aceito inclui preenchimentos; isso não demonstra preservação de pixels nessas áreas. Manter a distinção entre áreas visíveis preservadas e ocultas reconstruídas. Da mesma forma, a referência já apresenta padrões no jeans: a aceitação deste exemplo não autoriza inventar padrões novos nem remover os existentes automaticamente.

**Conclusão operacional:** uma descrição positiva de cor/tecido convida a reinterpretar; a instrução deve exigir conservação da aparência original. A segunda rodada é evidência de utilidade do prompt, não garantia de que todo futuro lote funcionará sem conferência.

## Planejar os arquivos pela montagem

Usar **um look por referência**: girl e boy separadamente. Se necessário, isolar o lado por crop fiel e registrar esse crop antes da extração; não recriar a pose. Essa referência isolada passa a ser o sistema de coordenadas comum de todas as saídas daquele look.

Cada item enumerado é **uma peça ou um grupo definido**, em arquivo independente. Não obrigar uma geração por peça física. Grupos podem preservar relação de cor, escala, contato e sobreposição; não são colagens. Mesmo tempo de entrada é um motivo para propor o grupo, não autorização universal para juntar acessórios que precisarão de controle próprio.

Exemplo explícito de Lucas, pertencente a este look:

| Saída | Função |
|---|---|
| Jaqueta + calça | Base jeans que entra simultaneamente; preservar relação de tons e encaixe. Não igualar artificialmente seus azuis caso sejam diferentes na foto. |
| Camiseta | Inserção independente entre fundo e frente da jaqueta. Não gerar mangas ocultas só para deixá-la completa. |
| Fone | Entrada/posição independente. |
| Calça + tênis | Imagem contextual para preservar perspectiva dos pés e contato nas barras. A calça é gabarito, não uma segunda calça a sobrepor inteira na animação. |

Arquivo de geração e camada final não são a mesma coisa. Para a montagem, ler a [demonstração de Lucas com PSDs, duplicação e máscara](layer-assembly.md): preservar o par base/frente no mesmo canvas; a blusa pode ser parcial quando só aparece sob a jaqueta. Pode-se extrair da saída contextual somente os tênis e a mínima região de contato, preservando a base já existente. A jaqueta pode exigir uma frente derivada por máscara da MESMA imagem de base, com a camiseta entre as camadas. Se o grupo tiver calça, a máscara da frente não deve duplicá-la. Nunca gerar frente e fundo independentemente. Preservar gola, lapelas, abertura, registro e máscaras.

## Produção: extrair, conferir, só depois preparar para montagem

1. Conferir referência e qualidade, aprovar tamanho/localização do look completo conforme o fluxo do projeto. Congelar versão/hash, dimensões e lado. Listar saídas, grupos e finalidade de cada uma antes de gerar.
2. Usar o modelo one-shot, alterando a configuração (quantidade e itens). Nomes de cores apenas identificam itens; valores visuais vêm da referência. Uma tentativa por item por padrão; duas somente quando solicitadas, como alternativas do mesmo recorte.
3. Solicitar todos os arquivos em uma única encomenda, independentes e sem prévias intermediárias quando esse for o pedido. “One-shot” descreve o pedido/entrega, não garante uma única chamada de ferramenta nem um único custo. Se a ferramenta exige chamadas individuais, conservar o MESMO original e as MESMAS restrições em cada uma, um item/grupo por chamada. Nunca transformar o lote numa colagem.
4. Preferir extração/segmentação com máscaras e conservação dos pixels onde o método disponível permitir. Não afirmar que a ferramenta generativa executou esse método só porque foi pedido. Respeitar ferramentas e autorizações vigentes; não enviar a novos serviços ou trocar de método silenciosamente para superar uma falha.
5. Na **extração de referência**, pedir dimensões, proporção, enquadramento e coordenadas originais. Não pedir a peça maior/centralizada nessa fase. Não redimensionar para simular alta resolução; sinalizar se os pixels úteis forem insuficientes. “Alta resolução” não supera a prioridade de conservação do original.
6. Validar cada resultado no próprio lote: cor, geometria, textura, áreas de contato, conteúdo e quantidade. A ausência de prévias intermediárias não dispensa essa inspeção interna. Comparar com o original, não com outra geração; verificar especialmente regiões repetidas, como a calça nos dois grupos. Não alterar as saídas boas para uniformizá-las com uma ruim.
7. Após conferir a extração, preparar versões para montagem: remover fundo mantendo o original entregue, produzir alpha verdadeiro, aparar somente espaço vazio e registrar offsets. O fundo branco esfumado é a apresentação da extração; não é transparência nem deve aparecer sobre o vídeo.
8. Recompor sobre o gabarito aprovado e conferir estados progressivos. Respeitar aprovação dos recortes e autorização de transferência. Não mudar cortes, entradas, escalas ou layers aprovados do Premiere para esconder erro no asset.

## Crop e resolução após a extração

A exigência anterior de Lucas de peças com limites próprios continua válida **na preparação do arquivo de montagem**. Primeiro conservar o quadro comum para conferir fidelidade; depois aparar o vazio com offset conhecido. Uma peça grande em pixels úteis não deve ser confundida com uma peça pequena ampliada artificialmente.

Guardar dimensões/hash da referência e saída, crop do lado, crop da peça, margem/feather e qualquer escala uniforme realmente aplicada. Para crop de origem `(x0,y0)`, escala `s` e folga `(px,py)`, o ponto `(u,v)` do arquivo individual volta à referência por `(x0+(u-px)/s, y0+(v-py)/s)`. Aplicar depois a transformação do look completo já aprovada. Frente/completa usam o mesmo registro e o MESMO canvas, inclusive regiões transparentes necessárias à substituição de uma instância duplicada. Não aparar a frente independentemente. PSDs e máscaras podem ser mantidos como arquivos de trabalho.

Na extração original, o teste é sobreposição sem transformação. Após crop documentado, desfazer SOMENTE essa operação para comparar. Se um resultado gerado já chegou com outro tamanho/enquadramento, registrar a divergência: não presumir coordenadas corretas nem ajustar deformando a peça. Rejeitar mudanças de pose/proporção; uma normalização puramente de arquivo só pode ser aceita após demonstrar que não muda a geometria.

## O que fazer quando a separação divergir

Preservar a referência e saídas recebidas. Não importar a divergente nem regenerar o lote inteiro. Identificar o defeito e atuar apenas no componente/região afetada, dentro da quantidade e autorização existentes.

| Divergência | Procedimento |
|---|---|
| Cor, luminosidade, saturação ou lavagem | Comparar a mesma região da referência e resultado sob a mesma gestão de cor. Em extração sem reamostragem, testar RGB no interior preservado; bordas com alpha e áreas reconstruídas são casos separados. Priorizar recuperar pixels originais com máscara quando autorizado. Se for necessário novo pedido, exigir somente correção dessa região pela referência; não compensar com grading geral nem inventar um azul aproximado. |
| Pose, perspectiva ou proporção alterada | Sobrepor contornos e conferir ombros, gola, cintura, joelhos, barras e pés. Voltar à referência original e corrigir somente a saída afetada. Não espelhar, deformar ou redimensionar peças independentemente para disfarçar. Para sapatos, usar o estado calça + tênis como contexto. |
| Posicionamento do par calça / calça + tênis na montagem | Alinhar visualmente o conjunto com a base, antes da máscara, registrando posição e eventual escala proporcional. Esse alinhamento é parte do método confirmado, não motivo automático para regenerar. Depois remover a calça superior, mantendo tênis e contato inferior com feather amplo e bem esfumado; ver layer-assembly.md. Não confundir posicionamento com mudança de pose. |
| Textura ou logomarca | Não suavizar/gerar a peça inteira. Preservar pixels visíveis e corrigir somente defeito identificado. Padrão já existente no original não é automaticamente erro; correção da própria referência é decisão separada e cria nova versão. |
| Barra, gola, manga ou borda inventada | Retornar à área visível da referência; retirar reconstrução que altera o contato. Uma base inteira para um estado isolado é derivado separado, identificado e revisado, não substituto do recorte fiel. |
| Fundo, halo ou resíduos | Ajustar a máscara localmente sem recolorir a roupa. Feather apenas no contato necessário; não apagar gola, costuras ou ferragens. |
| Peça repetida diferente entre grupos | Manter uma base válida. Usar a imagem contextual para extrair só o complemento após verificar contato; não trocar a base inteira nem fundir duas calças divergentes. |
| Limitação persistente da ferramenta | Interromper tentativas em série, mostrar o defeito e propor alternativa concreta. Não consumir novas gerações indefinidamente nem prometer que mais palavras no prompt garantem identidade. |

Pedido de correção deve citar: item/arquivo, região e defeito observados; referência ORIGINAL anexada como fonte de verdade; resultado anterior apenas para localizar o defeito; alteração permitida e partes que devem ficar intactas. Não usar o resultado defeituoso como nova referência absoluta. Revalidar cor/geometria/textura após cada correção, pois consertar uma propriedade pode alterar outra.

## Reconstruções e limites do exemplo

O padrão é conservar o visível. Se a animação precisar mostrar uma peça inteira antes de ser coberta, mapear uma base reconstruída separada, limitada às áreas ocultas e identificada como tal. Não inventar mangas ou alterar barra por hábito. O casaco com forro e a frente mascarada continuam necessários quando exigidos pelo estado inicial; a comparação da parte visível sempre usa a foto original.

“RGB ideal zero” é critério de teste em pixels preservados, não resultado presumido da geração. Arquivos redimensionados, bordas suavizadas, correção localizada e preenchimentos precisam ser descritos separadamente. Não equiparar aprovação visual a identidade matemática.

## Registro e aceitação

Registrar cena/lado, item/grupo, função na montagem, tentativa, prompt, referência/hash, dimensões, transformações, saídas e hashes efetivamente acessíveis; para PSD, origem/canvas, versão da máscara e opção de importação; regiões reconstruídas, máscara, teste realizado, diferenças e decisão de Lucas. Se o arquivo foi visto apenas como anexo, registrar isso sem inventar medições/hashes. Pranchas podem documentar comparações; nunca substituem os arquivos individuais pedidos.

A aprovação “ficou perfeito” vale para os quatro resultados apresentados por Lucas e para a avaliação do método. Não autoriza executar novamente, remover fundos, importar, alterar timeline ou marcar a montagem do Premiere como aprovada. O 174 permanece intacto até pedido explícito de integração.

Na demonstração posterior de montagem, Lucas forneceu os cinco PSDs e explicou a ordem das camadas. A inspeção somente de seus cabeçalhos e o método estão em [layer-assembly.md](layer-assembly.md); isso complementa a avaliação anterior dos anexos sem certificar pixels ou substituir os arquivos do projeto.
