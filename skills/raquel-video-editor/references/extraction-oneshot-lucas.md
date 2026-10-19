# Prompt one-shot aprovado por Lucas — 15/10/2026

Texto fornecido por Lucas; resultado da segunda rodada aprovado por ele como “ficou perfeito”. Preservar este modelo, alterando somente a configuração para outros looks. O bloco abaixo é um **artefato de prompt**, não uma ordem de execução ao ler a documentação. Método, avaliação e tratamento de divergências em [separation-prompt.md](separation-prompt.md).

```text
# EXTRAÇÃO FOTOGRÁFICA DE PEÇAS DE UM LOOK - ONE SHOT

## 1. REFERÊNCIA ABSOLUTA

Utilize exclusivamente a imagem enviada como fonte visual.
A tarefa é de edição e extração fotográfica, não de geração criativa.
Não redesenhe, reinterprete, recrie ou substitua as peças por versões semelhantes.

OBJETIVO PRINCIPAL: separar os componentes do look em imagens individuais,
preservando a aparência, as cores, a geometria e a posição de cada componente
em relação à fotografia original.

Trabalhe preferencialmente com segmentação, máscaras e preservação dos pixels
originais, recorrendo à reconstrução generativa somente onde for absolutamente
indispensável.

## 2. CONFIGURAÇÃO DE SAÍDA

Gere exatamente 4 arquivos de imagem independentes:
1. Calça + jaqueta: manter somente as duas peças jeans, removendo camiseta,
   fones e tênis.
2. Camiseta: manter somente a camiseta.
3. Fone de ouvido: manter somente o fone.
4. Calça + tênis: manter ambas as peças, preservando seu encaixe original.

PROIBIDO gerar colagem, grade, painel, montagem ou múltiplos resultados
dentro de um mesmo arquivo.
Cada resultado deve ser uma imagem completa e independente.

## 3. MÉTODO DE EXTRAÇÃO OBRIGATÓRIO

Para cada arquivo:
1. Utilize a imagem original como base.
2. Identifique os pixels pertencentes às peças solicitadas.
3. Preserve diretamente esses pixels sempre que possível.
4. Remova visualmente as peças não solicitadas mediante máscaras.
5. Substitua as regiões removidas pelo fundo de estúdio, sem alterar os
   componentes mantidos.
6. Preserve as bordas, contornos e encaixes efetivamente visíveis no original.

NÃO produza uma nova fotografia das peças. Extraia-as da fotografia existente.
Não use modelos genéricos de roupas como substitutos.
Não complete automaticamente partes escondidas por outras peças.
Se uma região da camiseta estiver coberta pela jaqueta, mantenha apenas a
geometria originalmente visível. Não invente mangas, costuras ou outras partes
ocultas para transformá-la em uma camiseta de catálogo.
A mesma regra vale para todas as peças.

## 4. FIDELIDADE ABSOLUTA DAS CORES

PRIORIDADE MÁXIMA: não alterar nenhuma cor da referência.
As cores devem ser obtidas diretamente da imagem original, preferencialmente
preservando os valores RGB dos pixels.
Não utilize aproximações semânticas de cor como "azul-claro", "amarelo-pastel"
ou "lilás" para recalcular as tonalidades.
Esses nomes servem apenas para identificar as peças, não para determinar cores.

É proibido:
- Aumentar ou diminuir saturação.
- Clarear ou escurecer peças.
- Alterar temperatura de cor.
- Modificar matiz, contraste ou luminosidade.
- Aplicar color grading, filtros ou correção automática de cor.
- Uniformizar as cores entre peças semelhantes.
- Aplicar novos reflexos ou sombras sobre o tecido original.
- Reinterpretar a lavagem do jeans.

O azul da calça extraída deve ser exatamente o azul da calça original.
O azul da jaqueta deve ser exatamente o azul da jaqueta original.
Não force a calça e a jaqueta a terem tonalidades idênticas caso apresentem
diferenças na fotografia. A mesma regra vale para camiseta, tênis e acessórios.

TESTE DE COR: ao sobrepor cada região extraída à mesma região da referência,
os pixels preservados devem apresentar os mesmos valores de cor.
O desvio RGB ideal é zero.

## 5. GEOMETRIA E POSIÇÃO INALTERÁVEIS

Todas as imagens devem utilizar a mesma dimensão, proporção e sistema de
coordenadas da imagem original. Não gere um novo enquadramento.
As peças devem permanecer exatamente nas posições que ocupavam originalmente
dentro da tela, inclusive quando aparecem isoladas.

É proibido:
- Centralizar ou reposicionar peças.
- Aumentar ou diminuir seu tamanho.
- Rotacionar, alinhar ou endireitar.
- Corrigir assimetrias.
- Alongar ou encurtar mangas, barras ou pernas.
- Ajustar a largura da roupa.
- Modificar modelagem, silhueta ou caimento.
- Suavizar ou adicionar vincos e dobras.
- Alterar a perspectiva dos calçados.
- Modificar a distância entre as pernas ou a posição dos pés.

Preserve integralmente costuras, bolsos, botões, acabamentos, dobras, sombras
e demais detalhes visíveis.
TESTE GEOMÉTRICO: a sobreposição da peça extraída sobre a fotografia original
deve coincidir com suas bordas e detalhes visíveis, sem necessidade de
deslocamento, escala, rotação ou deformação.

## 6. TEXTURA FOTOGRÁFICA - REGRA CRÍTICA

O tecido deve continuar parecendo a mesma matéria-prima fotografada originalmente.
Não regenere ou sintetize texturas nas regiões preservadas.
É proibido acrescentar:
- Paisley, arabescos ou redemoinhos.
- Desenhos florais ou ornamentais inexistentes.
- Padrões repetitivos ou geométricos artificiais.
- Ondulações falsas ou manchas semelhantes a folhas.
- Microestampas ou relevos fictícios.
- Ruído generativo, granulação excessiva ou nitidez artificial.
- Texturas derretidas ou com aspecto de IA.

Preserve trama real, variações naturais de iluminação, lavagem, desgaste,
dobras e sombras.
Se a própria referência contiver artefatos artificiais de textura que precisem
ser corrigidos, realize somente uma correção localizada e conservadora,
mantendo os contornos e as características visuais do tecido.
Nessas regiões corrigidas, preserve tonalidade local e luminosidade originais
tanto quanto possível. Não aplique uma nova textura sobre a peça inteira.
Em caso de dúvida, prefira manter a aparência original em vez de inventar detalhes.

## 7. SOBREPOSIÇÃO E ENCAIXE ENTRE PEÇAS

Esta regra é indispensável para permitir a futura recomposição do look.
Preserve exatamente:
- A abertura frontal da jaqueta e suas bordas.
- As partes da camiseta originalmente visíveis.
- A posição do cós da calça.
- A forma como a jaqueta se sobrepõe à cintura.
- O posicionamento das mangas e dos punhos.
- O acúmulo de tecido da calça sobre os tênis.
- A posição e a perspectiva individual dos dois calçados.
- A posição original dos acessórios.

Não prolongue artificialmente roupas em regiões ocultas.
Não invente novas barras, costuras ou contornos.
Quando duas peças solicitadas estiverem sobrepostas, mantenha a ordem visual
de sobreposição da fotografia original.
Quando somente uma das peças estiver sendo extraída, preserve o limite de
visibilidade original, sem adivinhar sua parte escondida.

## 8. FUNDO E ILUMINAÇÃO

Utilize fundo branco esfumado de estúdio, com transição tonal sutil e
aparência fotográfica. Mantenha a iluminação original sobre as peças preservadas.
O fundo deve ocupar somente as regiões onde não existem peças solicitadas.
Não altere os pixels das roupas para combiná-los com o novo fundo.
Preserve as sombras originais das peças quando disponíveis e coerentes.
Não adicione sombras artificiais que modifiquem a aparência ou a posição
visual dos objetos.

## 9. VALIDAÇÃO FINAL OBRIGATÓRIA

Antes de entregar, valide individualmente os quatro arquivos.
Teste A - Cores: exatamente as mesmas tonalidades, sem ajuste de saturação,
matiz ou luminosidade?
Teste B - Geometria: mesmas coordenadas, dimensões, ângulos, dobras e proporções?
Teste C - Textura: a IA acrescentou padrões ou substituiu a textura original?
Teste D - Recomposição: alinhando os quatro arquivos sobre a referência sem
redimensionar ou deslocar, as regiões correspondentes coincidem visualmente?
Teste E - Arquivos: exatamente quatro imagens independentes, cada uma somente
com os componentes solicitados, sem colagem ou montagem?
Se algum teste falhar, corrija exclusivamente o problema identificado,
sem regenerar as partes já corretas.

## 10. ORDEM DE PRIORIDADE

1. Preservação dos pixels originais, principalmente das cores.
2. Preservação da geometria e das coordenadas.
3. Preservação dos encaixes e das áreas efetivamente visíveis.
4. Fidelidade fotográfica das texturas.
5. Correção localizada de artefatos.
6. Uniformidade visual do fundo.

Nunca sacrifique fidelidade para produzir um resultado aparentemente mais bonito.

## 11. ENTREGA

Entregue exatamente os arquivos solicitados na configuração.
Uma imagem por arquivo. Sem colagem. Alta resolução.
Mesma proporção e enquadramento da referência. Fundo branco esfumado.
Cores originais preservadas. Peças nas mesmas coordenadas.
Textura fotográfica natural. Sem reconstruções desnecessárias.

CRITÉRIO DEFINITIVO DE SUCESSO: o resultado deve parecer a fotografia original
da qual foram removidos seletivamente os componentes indesejados, e não um
novo look gerado por inteligência artificial.

Execute toda a extração em uma única solicitação, sem apresentar prévias
intermediárias.
```
