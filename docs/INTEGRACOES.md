# Referências de acabamento — 13/10/2026

> Integração Premiere/MCP (15/10/2026): conexão e amostra testadas por outro assessor, conforme [relatório](PREMIERE_MCP.md). Fluxo confirmado por Lucas: primeiro XML, depois MCP. Preservar as limitações demonstradas; texto exibido não valida o estilo 101 nem sua edição pelo MCP. Não reinstalar nesta revisão documental. Direção em [fluxo vigente](FLUXO_EDICAO_PREMIERE.md) e limites atuais em [Premiere XML](PREMIERE_XML.md).

> Migração de armazenamento: raízes em `studio/storage.json`. Projetos atuais ficam em `Edit/<id>/project`; saídas de voz em `Edit/<id>/audio`, rosto em `face` e cabelo em `hair`. `face-base`, `hair-prepare` e `hair-render` podem escolher um novo diretório em Edit quando --work for omitido. As etapas seguintes recebem esse mesmo caminho. O 174 foi reiniciado: exemplos antigos e evidências em `analysis/` abaixo são históricos, agora sob `/Users/lucas/Movies/Vídeos/Edit/_editor/research/migration-20261013/analysis/`; não são configuração ativa nem promessa de execução desses experimentos antigos.

## Cabelo local deste editor

O método MatAnyone 2 com feather foi desenvolvido e avaliado localmente em `analysis/hair-validation/`. Não pertence ao Rosto Natural. Os controles reutilizáveis estão em `scripts/hair_controls.py`, com interfaces `hair_analyze.py` e `hair_finish.py`. Contrato, parâmetros por cena/trecho, cache, comandos e procedimento de integração: [HAIR_FINISHING.md](HAIR_FINISHING.md). O conector `scripts/hair_connector.py` integra os comandos `studio.py hair-*`: controles próprios em `finishing.json`, composição sobre a base anterior, associação reversível e invalidação por corte/controles/base. Preserva a análise original e mantém fundo, cabelo, maquiagem e áudio separados. Associação técnica não libera masters nem concede aprovação visual.

## Acervo

Diretório confirmado: `/Users/lucas/Movies/Vídeos/Edit`. Inventário: `analysis/finishing/inventory.json`. Encontrados 13 pares candidatos com arquivo `.mov` sem sufixo e `-facetune.MOV`. Isso não limita o acervo a 13: outros padrões de nome não foram pareados automaticamente.

Amostra 176: vídeos cru e FaceTune com 22,383333 s; WAV cru 22,388625 s; editado 22,384036 s. Dois frames a 2 s foram extraídos e inspecionados; enquadramento/expressão compatíveis nessa amostra e tratamento de pele visível. Isso não comprova estabilidade no vídeo completo nem alinhamento de todos os pares.

Áudio medido com FFmpeg (não escuta crítica): cru −31,46 LUFS, −13,43 dBTP; editado −14,90 LUFS, −0,84 dBTP. Dados em `audio-176-levels.json`. Não copiar um ganho fixo desse exemplo para toda gravação; o processador tem outras etapas.

## Voz Neural

Atualização (13/10/2026): `voz-neural-editor-v1.0.0`, aprovado por Lucas na comparação do 172, está integrado como padrão de novos jobs. Após aprovação do corte inicial, `render`/`compile` preparam e associam o áudio automaticamente, com versão fixa, duração exata e ganho adicional zero. Jobs existentes permanecem intactos; escuta e aprovação de cada exportação continuam separadas. Uso e comandos: [VOZ_NEURAL.md](VOZ_NEURAL.md). Evidência: `analysis/voice-editor-integration/REPORT.md`. O levantamento abaixo é histórico, anterior à validação e à integração.

Repositório local: `/Users/lucas/Documents/Codex/audio-neural`, remoto `https://github.com/lucasmef/voz-neural`, HEAD consultado `29f44a3d56c7490afdd4326b037d566a8477dfe7`.

Consultados README, README do fluxo independente e DEPENDENCIES.lock. Existe runner offline `independent_neural_flow_20260729/independent_voice_runner.py`, que documenta entrada WAV PCM e saída PCM 24-bit, mesma duração/taxa, estéreo dual-mono por padrão. O README registra RNNoise, DeepFilterNet e DSP próprio com dependências fixadas. Não foi executado nem reinstalado neste trabalho; os resultados publicados no repositório não são nova validação nossa.

Próximo adaptador: extrair voz do corte, executar runner com seus binários/modelos fixados, medir/escutar, registrar preset+hash e ligar saída com attach-finish. Conferir a localização real das dependências: README menciona também um caminho antigo `voz-neural`.

## Rosto Natural

Atualização local Metal (13/10/2026): conector implementado em `scripts/face_connector.py`, com `face-base`, `face-prepare`, `face-render` e associação verificada pelo `attach-finish`. Usa o runner atual de `/Users/lucas/Documents/Codex/rosto-natural`, não a cópia antiga de `analysis/face-validation`. Fluxo, restrições e repetição: [ROSTO_METAL.md](ROSTO_METAL.md). Evidência real de GPU, PCM e falhas: `analysis/editor-metal-integration/REPORT.md`. Integração exercitada em fixture isolada; não constitui aplicação ou aprovação do 174. O levantamento abaixo é histórico, anterior a essa execução.

Repositório informado por Lucas: https://github.com/lucasmef/rosto-natural . Consultados pelo conector GitHub: README (blob `968ac974694c4a9f5b69c1fbbbf798ed0169ee4f`), diretório tools e `tools/rosto_cli.cpp` (blob `7a4cbfe0f4f601f70360e94af258a1dac24d9e43`).

O README descreve núcleo offline e calibração com FaceTune; integração Adobe ainda tem dependências pendentes. A CLI consultada processa uma imagem PPM e recebe FaceMesh ou geometria; não é um processador de vídeo completo. Ela oferece parâmetros de pele, textura, tom, olhos, blush e lábios. Ferramentas de cabelo são separadas. Não clonado, compilado, instalado ou executado nesta etapa.

Próximo adaptador: decodificar frames, obter landmarks/máscaras, preservar rastreamento temporal e detecções entre quadros, processar, reencodar base sem alterar duração/áudio. Testar trecho curto antes do lote. Não rodar independentemente por frame com detecções instáveis. O orçamento de tempo precisa ser medido no Mac; o desempenho CPU relatado pelo README não é promessa de velocidade do nosso pipeline.

A política aprovada no outro projeto não deve ser transferida silenciosamente para uma nova versão do 174. Avaliar a aplicação concreta junto às referências de Lucas. Nenhuma referência privada foi enviada ao GitHub ou a um serviço de tratamento.
