# Acabamento com margens por tomada

Direção de Lucas em 14/10/2026: preservar liberdade de apertar ou alongar as junções depois do áudio neural, cabelo e maquiagem. Atualização aprovada em 15/10/2026: reservar margens na seleção, apresentar e aprovar o corte justo, depois tratar as janelas ampliadas. O corte justo não elimina a reserva de origem.

## Formato obrigatório dos intermediários de acabamento

Definição explícita de Lucas em 14/10/2026: maquiagem e cabelo devem ser processados sobre as tomadas selecionadas com margens reais, em **2160 × 3840, 60 fps constantes, ProRes 422 Standard (perfil 2)**, Rec.709 e PCM estéreo 48 kHz. Não usar ProRes HQ nem LT. Não tratar o bruto inteiro nem ampliar uma versão já tratada em 1440 × 2560 para chamá-la de 4K: extrair novamente do original 4K. Preservar as saídas de maquiagem e cabelo separadas, bem como máscaras, intervalos e procedência. Voz deverá acompanhar janelas por amostras quando o adaptador correspondente existir; o conector atual continua vinculado ao corte inteiro.

A resolução de acabamento é independente da composição/entrega, atualmente 1440 × 2560. Em uma entrega nessa resolução, uma fonte 2160 × 3840 permite escala de até 150% em relação ao enquadramento preenchido, sem exigir ampliação acima dos pixels disponíveis, desde que não haja outro recorte ou redução intermediária. A razão linear é 1,5×, não 2×. Uma entrega 4K não tem essa mesma reserva de zoom.

Color grading fica depois do acabamento. ProRes 422 Standard armazena 10 bits, mas não recupera informação do original 8-bit; os motores atuais usam RGB8 internamente. Não prometer processamento de cor integral em 10-bit. A análise de máscaras pode usar resolução própria, porém a imagem tratada e recomposta deve manter 4K real; revisar as bordas em 4K e no zoom pretendido.

O fluxo de janelas usa uma receita de processamento 4K independente da timeline editável. Os comandos legados sem `--window-work` continuam vinculados ao corte inteiro e ao formato do projeto; não usá-los para iniciar uma nova produção com margens.

## Fluxo desejado

1. Apresentar todas as tentativas e receber a escolha de tomadas.
2. Identificar, no bruto, a janela contínua útil de cada tomada, incluindo preparação/respiração e cauda. Preservar preferencialmente 1 segundo de vídeo e áudio reais no começo e 1 segundo no fim de cada cena/tomada; 0,5 segundo por lado é uma alternativa quando a janela útil for menor. A 60 fps, são 60 ou 30 quadros por lado. Limitar à disponibilidade real, sem incluir outra tentativa, e registrar a margem efetiva de entrada e saída em frames; se houver menos de 0,5 segundo, registrar a limitação em vez de inventar material.
3. Montar o corte refinado a partir do original, mantendo as janelas reservadas. Inspecionar waveform e apresentar o vídeo completo para aprovação separada. Escolha de tomadas não aprova o corte.
4. Após aprovação do corte, processar maquiagem e cabelo sobre as janelas ampliadas; voz usa o contrato atualmente disponível, sem prometer reconformação por janelas. Preservar mídia tratada, máscaras, controles e referência ao original. Aplicar grading somente à gravação, depois do acabamento, preservando a base tratada sem grading e a receita de cor. Conformar os subintervalos aprovados sem acrescentar pausas.
5. Após qualquer reordenação, revisar novamente cada junção: uma saída seca seguida de uma entrada seca pode causar uma troca brusca mesmo quando as cenas isoladas estavam boas. Usar a preparação, a respiração e o movimento reais disponíveis para dosar a transição. As margens são reserva de edição, não pausas obrigatórias na versão final. Não substituir margem por congelamento, repetição de quadros ou silêncio artificial. Para mudar uma junção dentro das margens, reconformar vídeo, áudio, máscaras e eventos a partir do material tratado preservado. Não executar novamente a inferência só porque mudou a duração final.
6. Fora das margens, tratar apenas a janela necessária com contexto suficiente e rever a emenda. Modelos temporais e processadores vocais podem precisar de sobreposição ou de reprocessar a tomada afetada; não prometer que poucos frames isolados terão continuidade perfeita.

## Contrato necessário

Cada janela deve guardar cena/tomada, SHA-256 do bruto, intervalo original semiaberto, fps, dimensões/cor, intervalo útil e margens reais, hashes de mídia/máscaras/preset/modelo, offsets de áudio em amostras e evidências. A timeline final guarda o intervalo utilizado dentro da janela e sua posição de saída. Eventos e legendas acompanham a origem da fala ao alterar a entrada; não apenas acrescentar duração à cena.

Voz: processar a janela com contexto, recortar por amostras e verificar o ruído/nível nas emendas. Não aplicar fade sobre consoantes, não duplicar respirações nem assumir equivalência entre processamento de tomada e de montagem inteira. A migração do contexto de processamento exige comparar a voz resultante, preservando o preset congelado.

Cabelo: analisar a janela ampliada com seed revisto no novo primeiro quadro. Aparar os alphas e a base de forma idêntica na reconformação. Maquiagem: tracking contínuo da janela, proteções de oclusão e intervalos vinculados à origem. A saída final conserva a mesma grade de frames e amostras.

## Operação das janelas de maquiagem e cabelo

`scripts/finishing_windows.py` mantém uma receita congelada em `Edit/<id>/finishing-windows/<execução>/recipe`, com intervalos originais e offsets por cena em `windows.json`. Antes do handoff, a timeline editável fica em `Edit/<id>/project`. Após transferência registrada ao Premiere, o `.prproj` rege a montagem; receitas de acabamento permanecem imutáveis e não são outra timeline. Ver `docs/FLUXO_EDICAO_PREMIERE.md`. As janelas podem compartilhar um pacote ProRes com offsets independentes; não é necessário duplicar os bytes em quatro arquivos para reordenar as cenas.

1. Preparar plano JSON com `reviewed`, `notes` e `scenes: {"cena-1": [inFrame, outFrame]}` após examinar as margens reais. Rodar `studio.py window-init ID --plan PLANO --work PACOTE`.
2. Usar os comandos oficiais `face-base`, `face-prepare`, `face-render`, `attach-finish video`, `hair-prepare`, `hair-config`, `hair-render --quality production` e `hair-attach`, acrescentando `--window-work PACOTE` a cada comando e paths novos em `--work`. O plano de cabelo aponta a `PACOTE/recipe/project.json`; `fullSize` deve ser `[2160,3840]`. Seeds e oclusões devem ser revisados na janela ampliada; coordenadas da revisão facial são 4K.
3. `studio.py window-publish ID --work PACOTE` exige maquiagem com procedência, cabelo completo em 4K e verificações dos conectores. Sela evidências por hash e associa o pacote à timeline sem alterar seus cortes, looks ou legendas. Preserva a configuração anterior no histórico.
4. O compilador localiza cada cena por ID, fonte e intervalo original. Pode reordenar ou aparar dentro da janela sem refazer maquiagem/cabelo. Fora da janela ou com fonte/evidência alterada, recusa o uso. Não substitui silenciosamente por bruto ou proxy.

O áudio neural legado continua vinculado ao corte inteiro: esta implementação de janelas visuais não declara reconformação de voz implementada. Na mesma montagem, o WAV já verificado pode permanecer separado; mudar corte/ordem mantém o bloqueio de áudio incompatível. A futura implementação de janelas de voz deve processar com contexto e preservar alinhamento por amostras. Não adulterar hashes ou assumir aprovação estética pelo sucesso técnico.

## Caso 174 / entrada da cena 3

A versão anterior começava no frame original 5942. Inspeção da waveform em 14/10/2026 indicou aproximadamente 30 ms até o primeiro ataque de fala. Por pedido explícito de Lucas, a entrada passou a 5934: oito quadros reais recuperados (133,33 ms), saída 6191 e cena 2 preservadas. Não inserir congelamento, quadros repetidos ou silêncio artificial para substituir esse movimento. Foi necessário reprocessar voz, rosto e cabelo pelo vínculo atual ao corte completo. Evidências e versão anterior preservadas em Edit/174/reviews/join23-20261014-v1 e respectivos diretórios de acabamento. A nova prévia segue para revisão; execução autorizada não é aprovação estética. Não houve escuta direta pelo assistente nessa inspeção.
