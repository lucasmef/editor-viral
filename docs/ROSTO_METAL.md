# Rosto Natural Metal no harness

> Formato de acabamento definido por Lucas: tomadas com margens em 2160 × 3840, 60 fps, ProRes 422 Standard (perfil 2), nunca HQ ou LT. A entrega 1440 × 2560 é independente. Reextrair do bruto 4K; não ampliar acabamento menor. Contrato e limitações atuais em [acabamento com margens](../skills/raquel-video-editor/references/finishing-handles.md).
> Direção atual de Lucas (14/10/2026): nos próximos processamentos, preservar preferencialmente 1 s real antes e depois de cada cena/tomada (0,5 s quando a janela útil for menor), para ajustes posteriores do corte e mudanças de ordem. Registrar as margens disponíveis e rever as junções após reordenar; a reserva não é uma pausa obrigatória na montagem. Ver [contrato de margens](../skills/raquel-video-editor/references/finishing-handles.md). Os comandos legados abaixo vinculam a saída ao corte completo. Para maquiagem/cabelo usar a receita 4K com `--window-work` e `window-publish`, descrita no contrato. Janelas de voz ainda exigem adaptação. Não prometer reaproveitamento automático nem alterar hashes para contornar essa limitação.

> Migração de armazenamento: raízes em `studio/storage.json`. Projetos atuais ficam em `Edit/<id>/project`; saídas de voz em `Edit/<id>/audio`, rosto em `face` e cabelo em `hair`. `face-base`, `hair-prepare` e `hair-render` podem escolher um novo diretório em Edit quando --work for omitido. As etapas seguintes recebem esse mesmo caminho. O 174 foi reiniciado: exemplos antigos e evidências em `analysis/` abaixo são históricos, agora sob `/Users/lucas/Movies/Vídeos/Edit/_editor/research/migration-20261013/analysis/`; não são configuração ativa nem promessa de execução desses experimentos antigos.

Conector: `scripts/face_connector.py`, integrado em `scripts/studio.py`. Motor externo existente: `/Users/lucas/Documents/Codex/rosto-natural/integrations/editor-metal-v1/runner.py`, executado pelo Python desse repositório. Usa Metal explicitamente, sem fallback CPU, sem Adobe e sem instalação de dependências no editor. F5 v004 permanece experimental. A associação não aprova acabamento nem exportação.

## Fluxo por montagem

Execute na raiz do editor, somente dentro da etapa autorizada. Substitua `JOB` e escolha um diretório **inexistente** para cada versão. Não execute o exemplo sobre o 174 por inferência.

```sh
.venv/bin/python scripts/studio.py face-base JOB --work analysis/face-validation/JOB-metal-v001
```

A base usa os originais registrados por hash e a ordem, início e duração de cada cena. Não usa proxies, acabamento anterior, legendas, stills, ganho de áudio ou voz tratada. No modo legado, saída na resolução do projeto. No fluxo obrigatório de janelas, usar a receita 2160×3840 com `--window-work`; 60 fps, ProRes 422 Standard progressivo, Rec.709 limitado, SAR 1, sem recorte; ajusta proporção com padding. Esta versão aceita fontes explicitamente Rec.709; não converte HDR. Intermediário de áudio é PCM float32 estéreo 48 kHz, preservando float32 em vez de reduzir a PCM16. O processamento interno do motor ainda usa RGB8; o contêiner 10-bit não representa precisão interna de 10-bit.

Inspecione a **base desta montagem** em sequência. Copie `review-template.json` para uma revisão própria, registre oclusões reais, mantenha todos os cortes indicados e preencha `reviewed: true` e `reviewNotes` somente após a revisão. Coordenadas referem-se à resolução da base; frames são locais à montagem. Consulte o README do motor para intervalos e máscaras. Hands não detecta pompom. Use retângulos/bypass explícitos onde necessário; não copie cache, exclusões ou override do 176. O template deliberadamente nasce sem revisão.

```sh
.venv/bin/python scripts/studio.py face-prepare JOB --work analysis/face-validation/JOB-metal-v001 --review /caminho/absoluto/review.json
.venv/bin/python scripts/studio.py face-render JOB --work analysis/face-validation/JOB-metal-v001 --compare-cpu
```

`prepare` executa tracking novo, com reinício nos cortes, sem `--reuse-v005`. `render` faz diagnóstico real de GPU e exige `--backend metal`. `--compare-cpu` é recomendado na primeira fixture e compara pixels com o controle CPU; acrescenta custo. Falha de GPU interrompe o fluxo e não associa mídia. Se o sandbox impedir Metal, execute no contexto macOS local com GPU permitido. Logs de diagnóstico são preservados por tentativa. Falhas parciais de render exigem nova versão; arquivos não são sobrescritos.

O conector valida relatório, hashes de fonte/base/análise/preset/binário/shader, backend/device, proteções e paridade quando solicitada. Decodifica independentemente todos os frames, confere PTS de 1/60 s e PCM exato. Salva `verified.json`; existência de `.mov` isolado não basta.

Revise a saída em relação à base, incluindo movimento, cortes, máscaras e oclusões. Crie um JSON de revisão temporal com os hashes reais de `base.json` e `treated.report.json`:

```json
{
  "outputSha256": "SHA256_DA_SAIDA",
  "baseSha256": "SHA256_DA_BASE",
  "editHash": "EDIT_HASH_DE_BASE_JSON_BINDING",
  "reviewed": true,
  "reviewer": "Nome de quem revisou",
  "notes": "Método, trechos observados, falhas e limites efetivos da revisão",
  "checks": {"temporalAlignment": "passed", "occlusions": "passed"}
}
```

Não preencha resultados por inferência. Revisão técnica não é aprovação estética; playback humano, escuta e checkpoints continuam necessários para produção.

```sh
.venv/bin/python scripts/studio.py attach-finish JOB video /caminho/absoluto/treated.mov --face-run analysis/face-validation/JOB-metal-v001 --temporal-review /caminho/absoluto/temporal-review.json --notes "Procedência e limites desta aplicação"
```

O comando usa o fluxo existente `attach-finish` e adiciona `videoConnector` à procedência. Conserva `audioMediaId`, ganho, legendas e layers editáveis. O renderer usa o vídeo tratado como base e a voz tratada separada como áudio, silenciando o áudio embutido quando existe `audioSrc`. Não altera aprovações. Master/release continuam nos gates existentes.

## Invalidação e separação do cabelo

`base.json` vincula fonte(s) SHA-256, segmentos, ordem, corte, dimensões/fps, versão/hash do conector e arquivos do motor. `prepared.json` sela base e análise; o cache do motor contém hashes de tracking/máscaras/revisão. Fonte, corte, formato, código ou motor alterado antes da execução exigem nova base/análise/revisão. Na compilação de um acabamento anexado, corte/formato, fontes originais, saída e evidências são novamente conferidos. Preserve a pasta da execução e a revisão temporal enquanto o job depender delas.

O resultado facial permanece separado de `hair_controls.py`/MatAnyone. Qualquer contrato compartilhado deve usar a mesma base SHA-256, dimensões, fps, frames e cortes, com espaços de coordenadas explícitos. Não aplicar máscaras de cabelo como máscaras faciais, nem encadear as saídas automaticamente. Composição conjunta e sua ordem exigem validação própria.

## Repetir a fixture real

Requer o acervo local `Movies/Vídeos/Edit/176.mov`, o motor instalado e as dependências existentes do editor. Nenhuma alteração é feita no job 174. A fixture cria um editor isolado, duas cenas de 24 frames (2 s e 10 s da fonte), still vermelho, legenda e voz separada com ganho 0,5.

```sh
.venv/bin/python scripts/test_face_connector_real.py --out analysis/editor-metal-integration/fixture-NOVA base
# Inspecione base.mov e crie fixture-NOVA/occlusion-review.json a partir do template.
.venv/bin/python scripts/test_face_connector_real.py --out analysis/editor-metal-integration/fixture-NOVA prepare
.venv/bin/python scripts/test_face_connector_real.py --out analysis/editor-metal-integration/fixture-NOVA render
.venv/bin/python scripts/test_face_connector_real.py --out analysis/editor-metal-integration/fixture-NOVA failures
# Revise treated.mov e crie fixture-NOVA/temporal-review.json com os hashes atuais.
.venv/bin/python scripts/test_face_connector_real.py --out analysis/editor-metal-integration/fixture-NOVA attach
.venv/bin/python scripts/test_face_connector_real.py --out analysis/editor-metal-integration/fixture-NOVA preview
```

`render` já ativa a comparação CPU. Para testar indisponibilidade real, execute esse estágio primeiro em contexto sem acesso à GPU: deve falhar no diagnóstico, antes de gerar saída. Repita no contexto permitido; logs permanecem separados. A fixture de falhas altera apenas cópias de fonte/cache e temporariamente seu próprio corte, restaurado em seguida. Use uma fixture nova para repetir a suíte; os testes também exercitam a recusa de sobrescrita. `--preview-name` permite nova prévia após falha do navegador, conservando a tentativa anterior.

Testes unitários: `.venv/bin/python -m unittest discover -s tests -p test_face_connector.py -v`. Verificações gerais: `pnpm check`, `pnpm test:harness`, `pnpm status`, `pnpm validate:final` (deve continuar bloqueando o 174 com checkpoints pendentes).

Evidência desta implementação: `analysis/editor-metal-integration/REPORT.md` e `fixture-v4/`. Os frames integralmente inspecionados da fixture não equivalem a revisão audiovisual contínua nem validam o 174.
