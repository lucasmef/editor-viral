# Padrão visual 101 — Lucas e Raquel

> Aplicação no Premiere (15/10/2026): posicionar primeiro o look completo transparente; registrar escala/posição e montar peças sobre esse gabarito. Legendas devem ser texto editável, com uma frase de calibração incluindo o halo final; legenda nativa ou MOGRT ainda precisam de validação. As regras visuais abaixo permanecem. Ver [fluxo vigente](FLUXO_EDICAO_PREMIERE.md).

Definido por Lucas em 14/10/2026 como o formato habitual dos vídeos. Segundo Lucas, o vídeo 101 teve muitos milhões de visualizações e é uma referência central de produção. Isso registra a justificativa editorial informada por ele, não uma auditoria de métricas.

Referência principal: `101-sem lembre-se.mov`, ID `m-1c25f89aac340b4d1de292dd2c9cf5404a5fe330832ee18f35e0765f68e31005`. O padrão é o ponto de partida habitual; um briefing específico pode mudar composição, presença dos títulos e posição da legenda. Não impor o formato a todos os vídeos.

## Regras e variáveis

| Elemento | Padrão | O que pode variar por vídeo |
|---|---|---|
| Segurança | 6% da largura em cada lateral e 6% da altura em cima e embaixo; área útil de 88% × 88% | A regra de 6% permanece, salvo instrução explícita de Lucas |
| Guias na prévia | Segurança e guias de altura sempre visíveis, inclusive em baixa resolução; retiradas do master | Alturas específicas do vídeo |
| Composição habitual | Girl à esquerda, boy à direita, Raquel entre/abaixo dos looks | Vídeos sem girl/boy, com outro número de looks, outros lados ou outra composição |
| Posição das roupas | Aproximar a roupa da borda segura correspondente, pelo contorno visível; preservar rosto, mãos importantes e legenda | Ajustes por cena/lado/peça, sem ultrapassar a segurança |
| Acessórios | Posição independente; uma bolsa pode ficar sobre a roupa e encostar na segurança | Não usar a bolsa como âncora que empurra toda a roupa para o centro |
| Escala dos looks | Medida pela roupa, sem contar o espaço transparente do PNG | Guia superior e inferior definidas para cada vídeo |
| Títulos girl/boy | Lettering ilustrado arredondado e cheio, girl rosa e boy azul-claro, volume suave, borda dupla clara e sombra, conforme a imagem fornecida por Lucas | Podem não existir. Posição superior junto à segurança, um pouco para dentro; não precisam coincidir com o centro dos looks |
| Legenda normal | Uma palavra por vez, minúscula, branca, contorno preto, conforme o 101; posição habitual central acima da cabeça | Posição e escala podem mudar conforme enquadramento/briefing |
| Continuidade | Só o primeiro frame do vídeo inteiro sem legenda; do segundo ao último frame, exatamente uma palavra visível, inclusive nas trocas de cena | Não criar nova abertura vazia a cada cena nem esperar o pompom |
| Omissões | Sem pontuação e com omissão seletiva de palavras funcionais, como “com” e “e”; preservar sentido e negações | Usar a política registrada no job; não remover palavras essenciais só para simplificar |
| Intervalos omitidos | Dividir a lacuna no ponto médio: prolongar a palavra anterior e antecipar a seguinte | Conservar os tempos de fala originais e aplicar a extensão visual na compilação |
| Destaque final | Mesma fonte, tamanho, cor, contorno e posição da legenda normal; apenas halo branco amplo e difuso por trás, como “rico” no 101 | Sem aumento da palavra, zoom, pílula, sublinhado ou troca de fonte por inferência |
| Cor | Grading somente na gravação da Raquel/cenário, nunca nos looks ou textos | Receita calibrada por gravação; referência de cor não autoriza inventar luz no abajur |

## Medir e registrar as guias dos looks

A guia superior marca o **topo da roupa**, não óculos, boné, fone ou outro acessório. A inferior marca a **barra da calça**, não o solado ou a ponta do sapato. Não medir pela caixa inteira do arquivo nem pela área ocupada pelos acessórios.

As duas alturas **não são universais**. Registrar no estilo do vídeo (`layout.lookGuides.top/bottom`, valores normalizados), junto da referência, frame/tempo consultado, dimensões e notas de medição em evidência externa. Medir uma roupa longa de referência. Saias e bermudas mantêm o comprimento natural, sem esticar para tocar a guia de uma calça longa. Todas as peças vinculadas de um look precisam preservar proporções e encaixes ao mudar a escala.

Manter as duas guias visíveis para revisão. Quando o posicionamento solicitado conflitar com rosto, legenda, acessórios ou segurança, revisar a composição e apresentar o conflito concreto; não resolver silenciosamente diminuindo todos os looks ou deformando as peças.

## Lettering e legenda: fidelidade visual

A imagem de girl/boy fornecida por Lucas é a referência do desenho. Não substituir por uma fonte genérica arredondada e declarar que ficou igual. Usar assets transparentes próprios, catalogados e versionados; conferir volume, forma das letras, bordas, sombra, tamanho e alinhamento visual. Aprovação do estilo de referência não aprova automaticamente cada reprodução gerada.

O destaque foi inspecionado no 101 em 3,6–3,8 s, na palavra “rico”: contorno preto nítido e área branca difusa ao redor/atrás. Comparar a exportação em tamanho de celular. O efeito não deve mudar a geometria da legenda normal.

A fonte exata do projeto original 101 não foi recuperada. Poppins Bold é a aproximação visual usada no 174; não registrá-la como metadado comprovado do 101. Separar sempre preferência confirmada, medição observada e valor de implementação ainda em revisão.

## Iniciar ou retomar um vídeo

1. Ler briefing, estilo do job, histórico e decisões anteriores. Usar o padrão 101 como ponto de partida habitual, respeitando qualquer exceção já definida.
2. Verificar se o vídeo terá títulos girl/boy, quantos looks aparecerão e em quais lados. Se o briefing já determinar outra composição, segui-lo sem perguntar novamente.
3. Conferir guia superior/inferior, posição da legenda e enquadramento da apresentadora. Se não houver decisão ou referência suficiente para uma variável, perguntar a Lucas **antes de fechar a composição**. Não copiar automaticamente as coordenadas do 174.
4. Concentrar as dúvidas reais em uma pergunta breve, por exemplo: “Neste vídeo seguimos o 101 com girl/boy? Qual referência usamos para as alturas das roupas e a posição da legenda?” Não pedir novamente valores já definidos no job ou no pedido atual.
5. Registrar escolhas e exceções na cópia de estilo do job; registrar medições/evidências em suas pastas externas. Preservar a distinção entre referência escolhida e aprovação da exportação.
6. Revisar todos os looks em cada etapa de entrada: topo/forro/frente, cintura/cinto, barra/calçado, acessórios, colisões com títulos/rosto/legenda e segurança. Corrigir defeitos claros sem exigir que Lucas os enumere um a um.

## Registro de calibração do 174 — não universalizar coordenadas

Canvas de trabalho: 1440 × 2560. Valores abaixo são a implementação corrente em revisão, não aprovação final do arquivo:

- Segurança: x=86,4..1353,6; y=153,6..2406,4.
- Guias: topo=355 px (0,138671875 da altura); barra=1730 px (0,67578125). Medidas visualmente no look masculino do 101, em 2,4 s, sem acessórios/calçados.
- Legenda: Poppins Bold 700, 70 px, branca, contorno preto 10 px; caixa x=420, y=950, largura=600; centro horizontal=720. Esse y é o topo da caixa tipográfica, não o primeiro pixel da letra.
- Girl/boy: imagens transparentes; centros x=295 e x=1150; topo das caixas y=153,6. Larguras atuais=220 e 235 px, respectivamente; alturas proporcionais aos recortes. Conferir contorno/sombra pelo alpha, não apenas pela caixa. Não impor esses valores a outro vídeo.
- Grading corrente: brightness=1,025, contrast=1,06, saturation=1,10, warmth=0,055. Receita do 174, não LUT universal nem recuperação exata da referência.
- Pompom e cliques: entradas visuais específicas da cena; a legenda contínua funciona independentemente deles.

Fonte editável do 174: `/Users/lucas/Movies/Vídeos/Edit/174/project/style.json`, `project.json` e `finishing.json`. Evidências: `reviews/guides-20261014-v1`, `scale101-20261014-v1`, `style-20261014-v2`, `fit-20261014-v1` e `captions-continuous-20261014-v1`, dentro de `Edit/174`.

Os PNGs atuais de títulos em `Assets/174/labels/reference-20261014-v2` são reproduções para revisão, não o arquivo original dos títulos da referência. Uma adoção futura como asset compartilhado deve preservar origem/versão e decisão real de aprovação.

## Relação com o software

Este documento define a direção editorial; [HARNESS.md](HARNESS.md) descreve os controles implementados. Cada vídeo possui sua própria cópia de estilo. Atualizar documentação ou padrões não deve alterar vídeos existentes.

`studio/default-style.json` ainda contém parâmetros genéricos legados de posição/tipografia e não é uma reprodução completa do 101. Ao iniciar um job no padrão 101, calibrar a cópia do job por este documento e pelas referências; não entregar os valores genéricos como se fossem o padrão aprovado. Configuração ausente de altura/posição não equivale a decisão de Lucas. Isso é uma obrigação do fluxo de trabalho, não um bloqueio automático já implementado.


## Padrão do projeto editor — 17/10/2026

Lucas esclareceu: “177 nao é projeto, é video. projeto é o editor”. Sua referência de girl/boy e margens define o padrão compartilhado do **editor**, aplicado no vídeo 177. Esta definição prevalece sobre as ressalvas anteriores quanto a esses valores não serem universais. Não altera automaticamente as cópias de estilo de vídeos anteriores.

Canvas de referência: 1440 × 2560. Segurança: 6% em cada borda. Guias de roupa: topo 355 px, alinhamento intermediário 820 px, barra da calça 1700 px. A guia intermediária é auxiliar e está implementada na prévia de looks; o renderer geral ainda suporta somente topo/barra. Não medir bonés, óculos ou calçados como limites da roupa.

Títulos gráficos transparentes existentes: girl rosa com centro X=355, topo Y=153,6 e largura 180 px; boy azul com centro X=1080, topo Y=153,6 e largura 190 px. Preservar as proporções e os recortes dos assets registrados em `studio/default-style.json`. Valores medidos aproximadamente na captura fornecida. Não substituir por texto simples.

Referência preservada em `/Users/lucas/Movies/Vídeos/Edit/177/reviews/composition-standard-20261017/reference.png`. Definir o padrão não aprova automaticamente o tamanho/posição de cada look.
