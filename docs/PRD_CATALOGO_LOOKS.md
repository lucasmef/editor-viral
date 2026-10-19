# PRD — Referências de roupas e validação dos looks

Atualizado em 16/10/2026 pelas correções explícitas de Lucas. Substitui o fluxo anterior de galeria extensa e as tentativas de recorte por silhueta.

## Ordem de trabalho

1. Ler o brief/roteiro e decisões do vídeo antes de pesquisar ou montar. No 177: `Edit/177/project/brief.json`. Não pedir novamente um texto já disponível nem usar ASR como substituto automático do brief.
2. Mapear as roupas-base de cada cena. Separar exigências do roteiro, propostas de modelagem e decisões já confirmadas.
3. Para cada produto, escolher **uma única foto representativa**, em que a peça correta esteja visível. Preferir foto isolada quando existir; foto com modelo também serve. Não baixar a galeria inteira por padrão.
4. Conferir correspondência entre foto, categoria, variante e link: se precisamos de calça, o link deve vender aquela calça, não a blusa usada pela modelo. Preservar URLs de produto com SKU/cor; limpar somente rastreadores. A URL da imagem não substitui a URL do produto.
5. Para a pesquisa masculina, seguir a quantidade e a diversidade da revisão vigente abaixo (a solicitação inicial de três produtos por item foi substituída). Selecionar produtos distintos, compatíveis com o roteiro e com ampla grade disponível na cor correta. Registrar tamanhos ofertados, disponíveis, indisponíveis e não verificados, data/hora e evidência. Priorizar grade completa; na falta, quase completa (no máximo um tamanho indisponível, sem excluir os centrais para favorecer a contagem). Não confundir variedade de tamanhos com quantidade de unidades em estoque. Se a loja não informar quantidade, ela é desconhecida. Não completar três opções com itens incompatíveis ou estoque não conferido: declarar o déficit.
6. Montar uma revisão simples por cena **com código, usando apenas retângulos das fotografias: blusa em cima, calça embaixo**. Sem máscaras, contorno de roupa, remoção de modelo/fundo, reconstrução, deformação ou tentativa de encaixar silhuetas. Um crop retangular pode focar a peça; preservar sua proporção. Havendo blazer e peça interna, mostrar retângulos separados identificados, sem simular vestir um sobre o outro. Manter uma foto por produto, reutilizada quando necessário.
7. Lucas valida as combinações. Só depois gerar as imagens estilizadas dos looks completos, vestidos sem modelo, na linguagem usada nos vídeos. A montagem retangular é apenas uma referência para escolha, não still de produção nem recorte aprovado.
8. Seguir o fluxo de edição vigente para qualidade, aprovação de tamanho/posição sobre vídeo, separação, montagem e transferência ao Premiere. A revisão de roupas não aprova esses checkpoints.

## Complementos de luxo

Lucas definiu que os complementos de cor serão **itens de luxo incluídos depois**. Não pesquisar esses complementos junto com as roupas-base, não improvisar substitutos, não tratá-los como falha da coleta atual nem exigir sua escolha para revisar as bases.

| Cena 177 | Base do roteiro | Complemento futuro de luxo |
|---|---|---|
| 1 | Jeans off + cinza | Burgundy |
| 2 | Jeans preto + branco | Camel |
| 3 | Listras + azul-marinho | Vermelho |
| 4 | Marrom + branco | Azul-claro |

O roteiro define cores, não todas as categorias/modelagens masculinas. Para pesquisa, a tradução proposta é calça embaixo e camiseta/polo/camisa em cima, preservando jeans quando explicitamente exigido. Calça marrom + parte superior branca na cena 4 é proposta para validação, não decisão previamente aprovada.

## Produtos femininos recebidos

Os sete links de Lucas estão preservados no manifesto da coleção `2026-10-16-sete-produtos`, com URL do produto, URL da imagem, variante, fonte local e SHA-256. Selecionar uma referência de cada para a revisão do 177; não expor todas as fotos antigas como interface principal.

- Cena 1: colete chevron cinza Animale (substitui a blusa cinza Renner) e calça barrel branca Riachuelo. Roteiro chama jeans off; loja chama Branco. Fotos e seletor confirmam branco apesar de denim médio no slug.
- Cena 2: jeans preto Riachuelo; regata branca Riachuelo e blazer branco Renner. Lucas indicou regata sob blazer. A regata abre em Branco apesar de bege no slug.
- Cena 3: camiseta listrada Riachuelo e pantalona azul-marinho Renner (variante denominada Azul na loja).
- Cena 4: saia midi pareô marrom Riachuelo + blusa ombro único franzida assimétrica off-white C&A, conforme links enviados por Lucas.

Estoque dos sete produtos femininos **não foi conferido** na coleta original. Não transferir a eles a verificação de estoque exigida agora para as opções masculinas.

## Armazenamento e dados

Código/documentação no editor; mídia e dados externos conforme `ARMAZENAMENTO.md`. Fotos existentes em `Assets/shared/products/2026-10-16-sete-produtos/`. Coleção de origem em `Edit/_editor/product-catalogs/2026-10-16-sete-produtos/catalog.json`. Não apagar os extras já baixados por inferência.

Revisão vigente: `Edit/177/reviews/looks-v2/index.html`, receita em `recipe.json`; a receita referencia arquivos e hashes existentes e registra crops retangulares e disposição. Não mantém timeline concorrente nem altera aprovações. Renderizador: `scripts/look_board.py` (Python com Pillow).

Cada produto precisa registrar: ID, cena/papel, loja/marca, título, categoria real, cor solicitada e cor da loja, código/SKU/variante observados, URL do produto, URL da foto representativa, path, dimensões, hash e data da coleta. Pesquisa masculina acrescenta preço/moeda observado, grade ofertada/disponível/indisponível/não verificada, horário/fuso, método/evidência e grau de compatibilidade. Não presumir disponibilidade por botão de tamanho existir. Verificar se está habilitado/selecionável e se não anuncia indisponibilidade; não comprar nem inserir dados pessoais para isso.

O catálogo final com **fotos e links de compra dos produtos exatos** é uma saída obrigatória futura, derivada dos mesmos registros. Não perder os links durante crops, montagem ou geração. Gerados devem manter vínculo com IDs/hashes das referências. Galeria antiga é histórico, não a revisão atual.

## Entregas e limites atuais

- Revisão retangular das bases femininas disponíveis, por cena, sem geração.
- Prompt separado para outro agente pesquisar roupas-base masculinas, três opções por item com estoque conferido e uma foto por produto.
- Complementos de luxo serão escolhidos depois.
- Automação/API futura deverá executar esse mesmo contrato; seleção automática, integração de catálogo e geração por API ainda não implementadas.

[Abrir revisão do 177](/Users/lucas/Movies/Vídeos/Edit/177/reviews/looks-v2/index.html) · [Prompt de pesquisa masculina](PROMPT_PESQUISA_MASCULINA_177.md)

Atualização: cena 2 é um único look com blusa branca + blazer branco + jeans preto, e não duas opções alternativas. Revisão v2 mostra as quatro cenas; complementos de luxo seguem para depois. Colete usa a foto anexada por Lucas e o link Animale associado; novas fotos da saia e blusa foram coletadas das respectivas páginas.


## Revisão masculina: contrato corrigido em 16/10/2026

Fonte: correções explícitas de Lucas na pesquisa masculina do vídeo 177. Estas regras prevalecem sobre a tradução inicial de categorias e sobre as revisões masculinas v1/v2, rejeitadas em parte. Não mudam os looks femininos nem aprovam produtos.

### Restrições que não podem ser relaxadas

- Lojas autorizadas: **Renner, C&A e Riachuelo**. Animale não entra na pesquisa masculina. Não ampliar lojas para preencher lacunas.
- Cena 1: **o item off-white/branco deve ser jeans/denim**, em qualquer posição. Pode ser calça, bermuda, camisa ou jaqueta jeans. Linho, sarja sem comprovação de denim, bomber de outro tecido e moletom branco não substituem jeans off. Branco e off-white continuam registrados separadamente segundo a variante real. A autorização para experimentar jaqueta branca não dispensou o tecido jeans.
- Cena 2: preservar jeans preto; branco é o contraponto. Cenas 3 e 4 preservam respectivamente listras + marinho e marrom + branco.
- Completar quantidades não justifica material errado, falta de estoque, combinação fraca ou repetição de um mesmo produto. Declarar lacunas concretas quando necessário.

### Seleção visual rigorosa

Para cada cena, pesquisar **duas direções normais distintas, uma bem descolada com moletom e uma com bermuda**. São direções de curadoria, não quatro pares travados. Moletom por si só não torna uma opção descolada; uma camiseta simples confeccionada em moletom ou uma jogger esportiva genérica não preenche automaticamente essa direção.

Inspecionar as fotos reais antes de incluir. Julgar o conjunto por modelagem, caimento, comprimentos, relação de volumes, peso e textura dos tecidos, nível de formalidade, contraste e foco visual. A seleção deve ser visivelmente bonita e vestível, não apenas cromaticamente possível. Registrar em dados/detalhes a decisão concreta de styling e por que as peças funcionam juntas. O juízo do agente é proposta, nunca aprovação de Lucas.

Evitar repetição de peças dentro e entre cenas. A cor pode reaparecer conforme o roteiro; isso não autoriza reutilizar a mesma camisa, camiseta ou calça como preenchimento de várias alternativas. Uma repetição tecnicamente possível não conta como opção nova nem como diversidade. As quatro direções precisam diferir visualmente, não apenas no rótulo. Não usar acessórios ou calçados fora do escopo para justificar uma base visualmente fraca. Não chamar uma opção de descolada sem evidência perceptível na roupa.

### Apresentação e interação obrigatórias

- Texto da cena **sempre visível**; não escondê-lo no modal de detalhes.
- Parte superior em cima e inferior embaixo, **ambas inteiras e legíveis na mesma tela**, sem rolagem para ver a segunda peça.
- Duas navegações independentes: deslizar/setas da parte de cima não altera a parte de baixo e vice-versa.
- **Dois botões de seleção**, um por peça. Salvar IDs por cena e posição separadamente; navegar não seleciona. Escolher ou desfazer uma peça preserva a outra.
- Nunca retornar ao botão único que escolhe um par. Direções de styling podem orientar a seleção, mas não travam combinações; uma combinação feita pelo usuário não herda aprovação estética automática.
- Pouco texto sobre as fotos. Título, tecido, preço, grade, faltas, evidência, links e justificativa ficam em **Ver textos**. Mostrar claramente lacunas e incompatibilidades do roteiro sem inundar a tela.
- Fotografias retangulares, proporção preservada, uma por produto. Nada de máscaras, remoção de fundo/modelo, colagens de silhuetas ou geração nesta etapa.
- Exportar preferências com IDs independentes de parte superior/inferior. Preferência não altera aprovações, timeline ou seleções do projeto.
- Validar visualmente a tela e o comportamento das duas escolhas; teste de sintaxe sozinho não comprova qualidade visual. Preservar versões e declarar o que ainda não foi verificado.

### Estado da aplicação destas correções

Nova revisão masculina: `Edit/177/reviews/pesquisa-masculina/2026-10-16-curadoria-rigorosa-v3/index.html`, com JSON/CSV e evidências na mesma pasta. A v2 permanece como histórico, não como curadoria vigente. A v3 retira os substitutos sem denim da cena 1 e a camiseta de moletom/jogger genérica apresentadas como descoladas. Introduz quatro produtos para novas propostas das cenas 2–4 e elimina repetição de IDs entre cenas. Fotografias e comparação retangular foram inspecionadas; lógica de escolhas independentes e estado vazio testados. Não afirmar aprovação estética de Lucas nem teste de layout completo em navegador.

Lacunas explícitas: cena 1 sem jeans off/branco elegível confirmado; cenas 2 e 4 com três superiores distintos, não quatro. Não ocultar a falta do tamanho central 44 na nova calça baggy branca (5/6). A pesquisa não prova ausência de alternativas no mercado.


## Quantidade de opções na geração de looks — decisão de Lucas, 16/10/2026

Antes de gerar novos looks montados, perguntar quantas opções Lucas quer **por cena/look**, quando o pedido não informar. Não assumir uma nem dez opções com base em templates anteriores. Se ele já indicar a quantidade, executar sem perguntar novamente. Distinguir esse número da quantidade de candidatos de roupas na pesquisa.

Neste pedido: três opções da cena 3 (cinto marinho de luxo) e três da cena 4 (marca do cinto visível e novas posições de sapatos/bolsa). Cenas 1 e 2 permanecem intactas. Preservar roupas-base reconhecíveis; variar os ajustes solicitados. Opções geradas não são aprovações.

### Pesquisa masculina — complemento de 16/10/2026

Revisão vigente da pesquisa: `Edit/177/reviews/pesquisa-masculina/2026-10-16-complemento-curadoria-v4/index.html`. Acrescentadas duas camisas Renner: boxy branca com bolsos/pesponto (cena 2, 4/5, falta PP) e oversized jacquard off-white (cena 4, 5/5). Propostas com as bermudas preta e marrom, respectivamente; fotos reais e comparação retangular inspecionadas. Agora são 28 produtos únicos; cenas 2 e 4 têm quatro superiores distintos. A cena 1 permanece sem jeans off/branco elegível confirmado mesmo ampliando a busca a jaqueta e bermuda nas três lojas autorizadas. Evidências e descartes no diretório da revisão; nenhum substituto sem denim incluído. Os produtos anteriores mantêm seus horários de verificação, sem alegar nova conferência. Escolhas independentes testadas; não representa aprovação de Lucas nem teste visual completo do HTML no navegador.

### Correção de critério por Lucas — cena 1, 16/10/2026

Lucas autorizou explicitamente sarja off/branca na cena 1 e pediu incluir os links Renner A-931610739/SKU 931610747, Renner A-638408267/SKU 638408515 e C&A 1117933-off_white. Esta decisão prevalece sobre a exclusão anterior de sarja sem prova de denim. Preservar a descrição comercial real do tecido; não exigir denim como condição desta seleção. Links incluídos em `Edit/177/reviews/pesquisa-masculina/2026-10-16-links-lucas-v5/`, na navegação independente da parte inferior da cena 1. Indicação do usuário não comprova estoque; fotos, cor e grade dos três registros estão explicitamente pendentes de conferência.

Correção concluída: `Edit/177/reviews/pesquisa-masculina/2026-10-16-fotos-cena1-v6/index.html` inclui as três fotos isoladas das páginas indicadas, com grade e preço observados. Calça Renner branca 5/5, bermuda Renner branca 5/5 e C&A off-white 7/7. A imagem isolada fornecida pela C&A traz marcação IA da própria loja; não foi gerada pelo agente. Não entregar cartões somente com links quando a revisão exige fotos. Conferidos arquivos/hashes, comparação visual das fotos e lógica independente dos seletores.
