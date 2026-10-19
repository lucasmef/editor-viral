# Voz Neural automática no editor

> Ordem vigente (15/10/2026): reservar margens na escolha das tomadas, aprovar o corte justo, então processar o acabamento. Desde 16/10/2026, `voice_windows.py` prepara voz por janelas e reconforma explicitamente a prévia; o conector automático legado permanece vinculado ao corte completo. Ver [fluxo vigente](FLUXO_EDICAO_PREMIERE.md).

> Direção atual de Lucas (14/10/2026): nos próximos processamentos, preservar preferencialmente 1 s real antes e depois de cada cena/tomada (0,5 s quando a janela útil for menor), para ajustes posteriores do corte e mudanças de ordem. Registrar as margens disponíveis e rever as junções após reordenar; a reserva não é uma pausa obrigatória na montagem. Ver [contrato de margens](../skills/raquel-video-editor/references/finishing-handles.md). Os comandos legados abaixo vinculam a saída ao corte completo. Para maquiagem/cabelo usar a receita 4K com `--window-work` e `window-publish`, descrita no contrato. Para voz por janelas, usar o adaptador explícito descrito ao final deste documento. Não prometer reconformação automática nem alterar hashes para contornar limites das fontes.

> Migração de armazenamento: raízes em `studio/storage.json`. Projetos atuais ficam em `Edit/<id>/project`; saídas de voz em `Edit/<id>/audio`, rosto em `face` e cabelo em `hair`. `face-base`, `hair-prepare` e `hair-render` podem escolher um novo diretório em Edit quando --work for omitido. As etapas seguintes recebem esse mesmo caminho. O 174 foi reiniciado: exemplos antigos e evidências em `analysis/` abaixo são históricos, agora sob `/Users/lucas/Movies/Vídeos/Edit/_editor/research/migration-20261013/analysis/`; não são configuração ativa nem promessa de execução desses experimentos antigos.

O preset aprovado por Lucas, `voz-neural-editor-v1.0.0`, é o padrão para novos vídeos. A aprovação foi dada após a comparação do 172 com a referência CapCut: “ok. congele esse preset e registre como versão aprovada”. Isso aprova a versão do processador, não a qualidade de cada gravação nem a exportação do 174.

## Uso normal

`init` e `assemble` copiam `studio/default-voice.json` para `finishing.json` do novo job. Depois de aprovar o corte inicial e as opções de looks (`preproduction`), o próximo `render` de prévia ou `compile` extrai o áudio dos originais na ordem do corte e executa o preset local automaticamente. Antes desse checkpoint, as prévias usam o áudio cru. Mesmo uma prévia de uma cena prepara o áudio do corte completo para manter o mesmo contexto de processamento.

Exemplo, substituindo `NOVO_JOB` pelo identificador real:

```sh
.venv/bin/python scripts/studio.py status NOVO_JOB
# Após a aprovação normal de preproduction:
.venv/bin/python scripts/studio.py render NOVO_JOB --out /tmp/NOVO_JOB-preview.mp4
```

Para preparar apenas a voz, sem renderizar vídeo:

```sh
.venv/bin/python scripts/studio.py voice-process NOVO_JOB
```

O status inclui `voice`, com versão e situação. Se corte, preset e adaptador continuarem iguais, a saída validada é reutilizada. Alterar corte ou ordem invalida o vínculo mesmo com duração total igual. Enquanto o novo corte aguarda aprovação, a prévia volta ao cru; após aprová-lo, o processamento gera uma nova pasta e preserva a saída anterior.

Jobs existentes não foram alterados. Para adotar o padrão explicitamente em um job antigo sem áudio tratado associado:

```sh
.venv/bin/python scripts/studio.py voice-process JOB_ANTIGO --enable
```

Esse comando continua exigindo o checkpoint inicial. Se já houver áudio associado, recusa a substituição. `fork` preserva a configuração do snapshot. Anexar áudio manualmente com `attach-finish JOB audio ARQUIVO --notes MOTIVO` desabilita o processamento automático naquele job para preservar a escolha manual.

## Contrato e rastreabilidade

- Pacote congelado: `.runtime/processors/voz-neural-editor-v1.0.0/`. Inclui runner, DSP, binários, Python, NumPy, preset, aprovação e fixture 172. Nenhuma instalação global ou serviço externo é necessário neste Mac.
- O perfil de cada job fixa versão e hashes do manifesto e da aprovação. Todos os arquivos e links internos do pacote são verificados antes da execução. Não editar o pacote: mudanças exigem outra versão e nova validação.
- Derivados: `Edit/<id>/project/finishing/voice/<execução>/`. O relatório guarda versão/preset, hashes de fontes e saída, corte, adaptador, segmentos e offsets em amostras, comandos, formato, tempo, LUFS e true peak medidos. Logs e diagnósticos ficam juntos.
- Extração dos originais verificados por SHA-256, nunca do proxy nem de uma base já tratada. Converte a 48 kHz, usa a média aritmética dos canais e concatena intervalos exatos do corte. Saída PCM 24-bit, dual-mono, 48 kHz, exatamente a mesma quantidade de amostras do corte.
- Timestamps de áudio/vídeo não alinhados a zero ou limites de corte não representáveis em amostras exigem reconformação explícita. O conector recusa esses casos; não corrige timing silenciosamente.
- A associação usa o mecanismo `attach_finish`, registra o hash do corte e impõe ganho adicional de **0 dB**. Não aplicar o ganho de comparação a −23 LUFS nem um ganho universal baseado no 176. A medição `loudnorm` apenas analisa a saída e não a modifica.
- O pacote foi congelado para macOS arm64. Outro sistema exige validar um runtime compatível como nova versão; não substituir dependências silenciosamente.

Processar não aprova escuta nem acabamento. O checkpoint de pós-produção continua exigindo revisão do resultado concreto. Master exige áudio compatível já preparado e checkpoints válidos; não inicia processamento de voz escondido durante a exportação final. Release continua vinculada à exportação exata.

## Verificação e recuperação

Regressão da versão congelada:

```sh
PYTHONDONTWRITEBYTECODE=1 .runtime/processors/voz-neural-editor-v1.0.0/python/bin/python3.12 .runtime/processors/voz-neural-editor-v1.0.0/verify.py --regression
pnpm check
pnpm test:harness
```

Ensaio real reproduzível, com corte curto de fala e job isolado em `analysis/` (não cria aprovações em jobs canônicos):

```sh
.venv/bin/python analysis/voice-editor-integration/exercise.py
```

Evidência da integração: `analysis/voice-editor-integration/REPORT.md`. Histórico e aceite: `analysis/audio-neural-validation/approved/`. A regressão antiga da fixture 65 continua pendente por ausência do arquivo original; o baseline reproduzido desta versão é o 172. A hipótese de troca de microfone não virou regra automática por número de vídeo.

Preservar no backup o pacote em `.runtime/processors/`, o registro de mídia, os jobs e seus derivados/relatórios. A cópia congelada de validação também permanece intacta. Mudar o padrão só afeta novos jobs; os existentes mantêm a versão copiada.


## Voz por janelas reais — implementação de 16/10/2026, vídeo 177

`scripts/voice_windows.py process JOB --window-work PACOTE --approval APROVACAO_CORTE --out EXECUCAO_NOVA` processa cada cena da receita ampliada separadamente com o pacote congelado aprovado. A aprovação específica em `project/cut-approval.json` contém scope `cut-only`, job, editHash, output/outputSha256 e userApproval; não concede aprovação aos looks nem ao acabamento. O conector legado automático não foi alterado.

Cada cena preserva input, WAV PCM 24-bit dual-mono 48 kHz com margens reais, diagnóstico e hashes. As janelas são as mesmas do vídeo 4K (`windows.json`); não se cria reserva preenchendo silêncio nem dividindo voz previamente aparada. Ganho adicional zero.

`conform JOB --report RELATORIO --out WAV_NOVO` monta uma voz derivada para a prévia usando intervalos exatos em amostras (800 por quadro a 60 fps). Preserva as fontes ampliadas e recusa cortes fora delas, outra fonte ou hashes divergentes. A associação explícita desabilita a voz automática legada neste job para evitar seu reprocessamento sem margens; perfil e evidências permanecem no relatório. Registra `finishing.voiceWindows`. Reconformar após nova escolha de corte continua sendo uma operação explícita; não existe reconformação automática escondida.

No 177, as quatro saídas têm a mesma contagem de amostras das respectivas entradas; correlação dos envelopes em blocos de 10 ms indicou lag zero. Isto não substitui escuta nem revisão labial. A integração das fontes por cena e dos links A/V no exportador XML e o teste de extensão/redução no Premiere continuam etapas distintas a validar no handoff; não usar o WAV de prévia como única fonte de intercâmbio.
