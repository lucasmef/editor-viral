# Transferência programática para Premiere

> Estado operacional atualizado em 17/10/2026: [EDITOR_OPERACAO_ATUAL.md](EDITOR_OPERACAO_ATUAL.md). As descrições datadas abaixo preservam o histórico; capacidades atuais, comandos e limitações estão no índice vigente. Nenhuma atualização migra o 177.

> Fluxo aprovado em 15/10/2026: [preparação e Premiere](FLUXO_EDICAO_PREMIERE.md). O exportador abaixo é a implementação existente, com limitações rejeitadas para as próximas entregas: PNGs do tamanho da sequência e legendas rasterizadas. Atualizar documentação não corrige o exportador. Preservar o pacote e os ajustes do 174; nenhuma reexportação/migração automática.

## Exportador legado, preservado somente com `--legacy`

O comando e as limitações desta seção descrevem o legado. Para produção nova, usar `--snapshot`, `--av-sources` e o contrato atual no índice operacional.

Legado: `scripts/export_premiere.py JOB --legacy --out DIRETORIO_EXTERNO_NOVO`.
Gera FCP7 XML (xmeml 5), mídia e snapshot independente; nunca altera o job ou registra aprovação. `--resume` retoma o snapshot congelado, não incorpora novas edições do Studio. Este snapshot não substitui automaticamente a fonte editável. Depois do OK e do handoff registrado, o `.prproj` passa a reger a montagem; alterações no Premiere não voltam automaticamente ao job. Não regenerar por cima de ajustes manuais.

Esta versão suporta montagem estática com cortes, PNGs, máscaras/crop/rotação estáticos e destaque glow. Recusa expressões nativas animadas, fades e ganhos não zero; esses casos exigem implementação específica. Não usar como exportador genérico sem conferir as limitações.

- Peças são RGBA na dimensão da sequência, rasterizadas pelo renderer existente. Máscaras e transformações são incorporadas ao alpha. Cada clipe pode ser movido, escalado e retimado no Premiere; o ponto de ancoragem inicial é o centro da tela, não o centro da roupa. O PNG não recupera pixels que a máscara removeu.
- Frente, fundo, acessórios e patches permanecem clipes independentes, na mesma ordem visual. Camadas de cenas sucessivas reutilizam trilhas quando possível.
- Legendas visuais são imagens por palavra. SRT é alternativa de texto, sem a aparência nem glow. Desligar as imagens ao usar SRT para não duplicar texto.
- Girl/boy são imagens separadas. Guias são a última trilha de vídeo e devem ser desligadas na entrega.
- Base visual de intercâmbio: 2160×3840, 60 fps, ProRes 422 perfil 2, com duração e margens da fonte tratada. Cor e enquadramento atuais são incorporados; a transformação de enquadramento reaproveita a fonte 4K, mas recorta as bordas. Original não é substituído e seu caminho/hash fica em original-media.json.
- O LUT aproxima a cadeia de filtros CSS (brightness, contrast, saturate, sepia), não é um efeito Lumetri nativo nem garantia de igualdade pixel a pixel entre gerenciamentos de cor. A interpolação e o codec podem produzir diferenças pequenas. Não aplicar grade.cube de novo na base já tratada.
- Voz e cliques permanecem separados. O áudio tratado não ganha margens automaticamente. Conferir duração física do efeito ao retimar.
- XML tem URLs absolutas percent-encoded. Manter media/ junto do pacote; ao mover, reconectar mídia ou regenerar URLs. A geração usa diretório externo em Edit/<job>/interchange.

Verificação: TypeScript, testes do harness, contagem/transparência PNG, referências XML existentes, limites por frame, codec/duração da base. Importação no Premiere é validação adicional, sem ajustes manuais da montagem. Não declarar playback ou fidelidade sonora sem escuta real. Exportação de intercâmbio não é master aprovado e não contorna render --master/release.

## Áudio e vídeo por cena com margens — decisão de Lucas, 15/10/2026

Aplicar aos próximos projetos/transferências XML. Lucas relatou que o vídeo chega separado por cena, com reserva para alongar os cortes, enquanto a voz chega inteira em um único arquivo. A entrega deve permitir aumentar ou diminuir cada cena com vídeo e áudio juntos, já sincronizados e cortados na timeline do Premiere.

- Preparar um arquivo de áudio por cena/tomada, com a mesma janela temporal de origem do vídeo correspondente, incluindo áudio real antes e depois do corte aprovado. Preservar preferencialmente 1 s por ponta, ou 0,5 s quando a janela útil for menor; registrar a disponibilidade efetiva. A margem utilizável em conjunto é limitada pelo material real disponível em ambos.
- No XML, colocar cada par de clipes de vídeo e voz no mesmo início/fim de timeline, com In/Out correspondentes ao corte aprovado dentro das fontes ampliadas. Vincular o par A/V para ajustes conjuntos no Premiere. Manter a reserva nas fontes, fora do trecho inicialmente exibido; não acrescentar pausas à montagem.
- Manter a voz editável e os SFX em clipes/faixas independentes. Um WAV único da montagem como única fonte de voz não atende à entrega solicitada; simplesmente dividi-lo nos cortes não recupera as margens descartadas.
- Preservar sincronismo por frames/amostras, origem, offsets e hashes por cena. A voz tratada precisa cobrir também as margens reais: o conector legado vinculado ao corte inteiro ainda exige adaptação e validação. Não preencher reservas com silêncio, repetir áudio, substituir por voz original sem decisão nem declarar essa capacidade implementada por esta documentação.
- Validar numa importação de teste: estender e encurtar entrada e saída de um par A/V dentro das reservas, confirmar vínculo, sincronismo labial/sonoro e ausência de lacunas, sobreposição indevida ou perda de palavras nas junções. Salvar e reabrir para conferir persistência. Registrar limites efetivos; checagem estrutural do XML não substitui essa verificação.

Esta decisão documenta o requisito futuro; não reexporta nem altera o 174 ou seus ajustes no Premiere. Implementação do exportador, adaptação da voz e teste de importação permanecem pendentes.

## Histórico de requisitos registrados em 15/10/2026

- Peças com dimensões próprias e registro geométrico; posição, escala e rotação editáveis no Premiere. Compensar offsets de transparência aparada para não deslocar peças. Comparar a recomposição ao look completo.
- Texto editável: validar legenda nativa ou gráfico/MOGRT com uma frase no padrão 101, incluindo contorno e halo final. SRT sozinho não comprova aparência; não entregar PNG de palavras como solução definitiva.
- Preservar base tratada 4K sem grade, receita de cor, margens e áudio separado. Grading deve atingir somente a gravação. Confirmar quais propriedades permanecem editáveis e quais foram incorporadas.
- Cenas sequenciais; referência de look completo e guias desativadas na exportação final. Sequências aninhadas são opção, desde que peças continuem acessíveis.
- Validar salvar/reabrir/exportar: geometria, crop, sobreposições, transparência, frames, texto e áudio. Registrar limitações reais; disponibilidade anunciada por um MCP não prova execução.
- Fluxo confirmado: XML para montagem inicial, depois MCP para ajustes. A integração existente foi configurada e testada por outro assessor; consultar [PREMIERE_MCP.md](PREMIERE_MCP.md). Preservar ajustes manuais e não reimportar XML por cima deles. No próximo projeto, validar a legenda editável no padrão 101 antes de aplicar ao conjunto; controle de texto/estilo pelo MCP ainda tem limitações.
- O harness atual não libera um master externo do Premiere automaticamente. Adaptar o contrato de candidatos/release para hash do export exato, evidências técnicas e aprovação real; não contornar gates nem forjar correspondência com o renderer.


Atualização de preparação, 16/10/2026: `voice_windows.py` já produz WAVs tratados individuais com a mesma reserva da receita visual (ver VOZ_NEURAL.md). Isso resolve a preparação das fontes de voz; ainda não certifica os links A/V ou o teste de extensão/redução no Premiere. Ao exportar um job com `finishing.voiceWindows`, usar os WAVs ampliados do relatório por cena, não o WAV conformado de prévia.
