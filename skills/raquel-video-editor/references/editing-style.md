# Linguagem de edição — referências e evolução

## Padrão confirmado em 14/10/2026

Lucas definiu o 101 como o formato habitual, com exceções por vídeo. O contrato atual está em [Padrão visual 101](../../../docs/PADRAO_VISUAL_101.md). As observações históricas abaixo não substituem essa direção: guias de topo/barra, títulos e posição da legenda precisam de definição por job; 6% de segurança é a regra fixa.

## Evidência e limites

Base: 10 vídeos examinados por amostras visuais nesta conversa (101, 176, 169, 168, 143-claro, 81, 16-04 calça marrom, 120-new, 127 e 41). Para 120-new, 127 e 41 foram reutilizadas pranchas existentes, reinspecionadas visualmente. 101 e 176 também tiveram transcrição automática local e amostragem mais densa de suas aberturas. Isso não equivale a escuta crítica, inspeção de todos os quadros, análise de métricas ou engenharia reversa integral do Premiere.

## Formatos observados

- **101 / 176:** duas colunas girl à esquerda, boy à direita, apresentadora central abaixo; looks começam por peças e recebem complementos. Legendas pequenas próximas/acima da cabeça. Os dois lados expressam a mesma lógica cromática, com modelagens distintas.
- **120-new:** boy à esquerda e girl à direita. Prova de que a orientação não é universal.
- **168 / 169:** uma coluna grande à esquerda e apresentadora à direita. Trocas de parte superior, bolsas, sapatos e outros acessórios enquanto bases podem permanecer.
- **143-claro:** entradas sucessivas de top e parte inferior; alterna para nova combinação.
- **81:** componentes distribuídos acima da cabeça; acessórios completam o conjunto. Legenda pode ficar mais abaixo.
- **41:** vestido como âncora vertical, grupo de acessórios ao lado.
- **127:** também há fotos com modelos e círculos de cor. Não converter automaticamente tudo em ghost mannequin.
- **16-04 calça marrom:** peça-base e camisetas empilhadas, título fixo e borda branca. É um formato mais antigo; não impor seus efeitos aos recentes.

## Exemplo temporal verificável — abertura do 101

Quadros extraídos: 0,00 a 5,10s em passos de 0,30s.

| Momento amostrado | O que aparece |
|---|---|
| 0,00s | Apresentadora e rótulos girl/boy; roupas ainda ausentes |
| 0,30s | Duas bases cinza |
| 1,50s | Tops brancos completam as bases |
| 2,10s | Legenda “adicione”, ainda sem o acento completo |
| 2,40s | Acessórios burgundy; bases e tops permanecem |
| 3,60s | Estado completo; legenda “rico” |
| 3,90s | Troca de bloco, breve tela sem looks |
| 4,20s | Tops rosa-claro iniciam o próximo bloco |
| 4,80s | Partes inferiores bege completam os tops |

Whisper posicionou “branco” em ~1,26–1,74s e o termo reconhecido incorretamente como “borgade” em ~2,22–2,78s. Há correspondência aproximada entre menção e aparecimento. Não deduzir latência fixa, frame exato, duração de animação ou curva de easing a partir dessas amostras.

## Decisões de implementação

- **Confirmado pelo usuário:** vídeo 174 segue o estilo do 101; screenshots do 174 valem pelas cores, styling rejeitado; exportação ProRes, 2K vertical, 60 fps.
- **Observado:** entradas progressivas associadas à fala, bases persistentes, pares de looks, legenda curta.
- **Proposta inicial:** cortes/entradas simples até medir animação; alvos de posição ajustáveis sobre o bruto; PNGs separados por entrada. Não é uma afirmação sobre as configurações originais do Premiere.
- **Ainda não identificado:** fonte exata, easing/duração dos efeitos, tratamento de áudio/rosto/cor, aceleração e preferência de takes. Não aplicar filtro ou música por suposição.

## Ajustes incrementais

Cada correção deve registrar vídeo/cena afetados, pedido, alteração e resultado da revisão. Promover a regra recorrente só quando o pedido for geral ou quando novos exemplos sustentarem a generalização. Preservar exceções de layout e evitar regras que engessem o styling.

## Calibração de escala por roupa — 174, 14/10/2026

Medir o topo da roupa e a barra da calça longa da referência, excluindo acessórios, sapatos e padding transparente. Escalar todas as peças do mesmo look juntas, mantendo encaixes e proporções. Não reduzir o conjunto inteiro apenas porque o canvas PNG é largo: conferir os limites visíveis do alpha. Saias e bermudas mantêm o comprimento natural, usando a escala da roupa longa da mesma cena; não alongar peças curtas até a guia inferior. Conferir os oito looks sobre a apresentadora e manter 6% de segurança em cada borda. Guias não são aprovação automática de encaixes.

No 174, a legenda normal deve reproduzir visualmente a referência 101 em tamanho, branco, contorno preto e posição; identificar a fonte por comparação quando não houver projeto original e registrar essa limitação. Destaque final da legenda e color grading continuam em validação separada.
