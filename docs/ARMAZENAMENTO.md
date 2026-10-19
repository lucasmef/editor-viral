# Armazenamento, preservação e retomada

> Atualização de 15/10/2026: referências ao reinício vazio do 174 abaixo são históricas. Preservar a produção e os ajustes atuais. Após handoff autorizado e registrado, o `.prproj` é a fonte da montagem; `Edit/<id>/project` preserva preparação, procedência e decisões, sem manter uma timeline concorrente. Ver [fluxo vigente](FLUXO_EDICAO_PREMIERE.md).

Definição de organização de 13/10/2026, com raízes externas explicitamente definidas por Lucas. Implantado no harness: configuração em studio/storage.json, jobs e catálogo externos, staging/cache externo, saídas por execução e promoção do master liberado para Prontos. O 174 foi reiniciado vazio a pedido de Lucas.

## Categorias e destinos

Todas as mídias e dados dos vídeos ficam fora da pasta do código do editor. Raízes oficiais informadas por Lucas (os espaços e o til do caminho de iCloud são literais, sem barras de escape no catálogo):

| Categoria | Raiz oficial |
|---|---|
| Assets | `/Users/lucas/Movies/Assets` |
| Edit | `/Users/lucas/Movies/Vídeos/Edit` |
| Source | `/Users/lucas/Movies/Vídeos/Source` |
| SoundFx | `/Users/lucas/Movies/Vídeos/SoundFx` |
| Prontos | `/Users/lucas/Library/Mobile Documents/com~apple~CloudDocs/Vídeos/Prontos` |
| Cache | `/Users/lucas/Movies/EditorGpt/Cache` |

Não criar cópias concorrentes dessas raízes dentro do editor. Subpastas abaixo são a organização atual. Arquivos históricos do acervo do usuário não foram renomeados.

```text
Source/                         originais preservados, nomes originais
  <sessão>/                     manter sessões já existentes, como 02-10
Assets/
  shared/                       materiais reutilizados em vários vídeos
  174/
    originals/                  PSDs e imagens recebidas/geradas originais
    selected/                   peças PNG com alpha usadas na edição
    options/                    alternativas que sustentam escolhas registradas
Edit/
  _editor/                      catálogo compartilhado de mídia, fora do código
    media.json
  174/
    project/                    brief, timeline, estilo, histórico e aprovações
    audio/<run-id>/              voz tratada e seus registros de processamento
    finishing-windows/<run-id>/  receitas congeladas e pacotes 4K com margens; preservar evidências
    face/<run-id>/               base facial tratada, controles e evidência
    hair/<run-id>/               etapa de cabelo independente, máscaras e controles
    reviews/<revisão>/           prévias, imagens e comparações usadas para decidir
    candidates/<revisão>/        master candidato, ainda não liberado
SoundFx/                        biblioteca existente de efeitos sonoros
Cache/                         raiz externa Movies/EditorGpt/Cache
  174/<etapa>/<chave>/           somente derivados com regeneração comprovada
Prontos/                        destino existente no iCloud
  174/
    v001/                       somente exports liberados desta versão
      174-v001-master.mov
      174-v001-entrega.mp4       apenas se essa versão de entrega for necessária
```

As pastas são categorias lógicas. Um material pode estar local ou arquivado sem mudar de identidade. Localizações são catálogo, não identidade: o ID permanece SHA-256. Sessões de Source podem servir a vários jobs; não duplicar nem mover bruto para uma pasta por vídeo.

`<run-id>` deve identificar uma execução imutável, incluindo versão/corte nos registros. Uma nova tentativa recebe novo diretório. Nenhuma saída sobrescreve a aprovada.

## O que preservar

| Classe | Exemplos | Política |
|---|---|---|
| Original | vídeo bruto, gravação de áudio independente | Preservar bytes originais; pode ficar offline depois de arquivado e conferido |
| Asset editorial | PSD, PNG selecionado, imagem original gerada, fonte/licença, SFX usado | Preservar a versão exata; geração por IA não garante recriação idêntica |
| Acabamento associado | WAV neural/CapCut utilizado, FaceTune/Rosto Natural aplicado, resultado de cabelo | Preservar, mesmo sendo tecnicamente derivado; pode arquivar com os registros necessários |
| Decisão e evidência | escolhas, revisão visual/sonora, presets, relatórios e arquivos examinados | Preservar para explicar e retomar a versão aprovada |
| Master liberado | ProRes final e versões de entrega aprovadas | Guardar separadamente em Prontos; nunca classificar como cache |
| Derivado regenerável | extração WAV sem tratamento, frames de trabalho, staging Remotion, proxy automático | Descartável somente com receita, fontes e dependências disponíveis e sem uso como evidência insubstituível |
| Runtime/modelos | ambiente Python, pesos, binários, fontes do renderizador | Instalação compartilhada versionada; não misturar com cache por vídeo; arquivar versões não recuperáveis |

Áudio final não significa somente o áudio embutido no master: o WAV tratado separado pertence ao kit de reedição em Edit. Músicas originais pertencem a Assets/shared; SFX pertencem à raiz SoundFx existente; as posições e ganhos pertencem ao job. Áudio capturado separadamente pertence a Source. Extração do bruto sem alteração pode ser cache quando reproduzível.

Maquiagem e cabelo permanecem etapas separadas. Máscaras automáticas podem futuramente ser cache, mas máscaras corrigidas manualmente e suas fontes são material editorial. Enquanto o conector exigir a análise para validar/recompor a saída, ela é uma dependência preservada, ainda que se chame `cache.json`.

## Projeto e mídia não são a mesma coisa

O editor em `/Users/lucas/Documents/Codex/editor` contém apenas o software: código, scripts, testes/fixtures sintéticas, skills, documentação, configuração das raízes, padrões e dependências necessárias ao funcionamento. Materiais reais de vídeos, resultados de testes com esses materiais, prévias e caches de processamento ficam fora dele.

Organização atual de metadados:

```text
/Users/lucas/Movies/Vídeos/Edit/
  _editor/media.json             catálogo compartilhado: IDs, locais e arquivos
  174/project/                  fonte de verdade deste vídeo
    brief.json
    looks.json
    project.json
    style.json
    finishing.json
    history/
    revisions/
    approvals/
    look-reviews/
    releases/
```

`jobs/174/` e `library/assets/` foram retirados do editor. O job novo é a única fonte editável e continua acessível pelo ID 174; nenhum corte, look ou aprovação foi herdado. O catálogo compartilhado em Edit evita registrar o mesmo arquivo separadamente em cada vídeo.

Backups precisam incluir os documentos dos projetos, catálogo, código/lockfiles, referências necessárias e mídias preservadas. Um snapshot do manifesto não contém automaticamente todos os bytes de vídeo/modelos necessários.

Os relatórios e hashes dos finais ficam em `Edit/174/project/releases/` e nas evidências preservadas. Assim Prontos continua contendo somente arquivos finais. O comando release promove um candidato para Prontos por cópia verificada, registrar sua localização e conservar a rastreabilidade da exportação exata. Copiar para Prontos não concede aprovação.

Caches de mídia, extrações, staging/public-dir do Remotion, bundles de render e testes temporários devem usar `/Users/lucas/Movies/EditorGpt/Cache`. Não deixar mídia real em `public/` do editor. Ambientes e modelos necessários ao software têm política de instalação própria; não são descartáveis só por poderem ser baixados novamente.

## Estados independentes

Separar a política de retenção do estado físico e da decisão criativa:

- Retenção: preservar / regenerável / ainda não classificado.
- Disponibilidade: local / arquivado conferido / offline / ausente sem cópia comprovada.
- Uso editorial: opção / selecionado / associado / aprovado / substituído.

Arquivo substituído não vira lixo automaticamente: uma revisão antiga ou outro vídeo pode usá-lo. Uma análise de limpeza deve considerar jobs atuais, snapshots, forks, releases e evidências, não só o manifesto atual.

## iCloud e reconexão

O arquivo preservado pode sair do disco local e continuar sendo parte do vídeo. Antes disso, registrar destino, tamanho e SHA-256; conferir uma cópia acessível e arquivar o conjunto de dependências. O harness atual registra endereços e confere conteúdo, mas não faz upload, download nem remoção local.

Para liberar espaço de itens sincronizados, usar a operação do serviço que mantém o arquivo na nuvem; não confundir com apagar o item sincronizado. Registro de um path de iCloud não comprova upload concluído nem substitui backup independente.

Após baixar, `studio.py relink MEDIA_ID CAMINHO` confere SHA completo. Para os conectores, a mídia principal sozinha não basta: relatórios, máscaras e caminhos de execução também precisam estar disponíveis. Os novos pacotes já são criados em Edit. Se um pacote de acabamento for movido para outra raiz, seus paths de trabalho e controles também precisam ser reconectados explicitamente; relink só da mídia principal não migra um pacote completo. Não editar relatórios imutáveis para fingir que seus hashes continuam válidos.

## Migração executada

- Originais em Source e arquivos existentes em Edit/SoundFx/Prontos ficaram intactos. O bruto do 174 foi conferido por SHA-256 e segue registrado no catálogo, sem estar selecionado numa timeline.
- O 174 ativo em Edit/174/project está vazio. Voz Neural aprovada é padrão, aguardando corte aprovado; rosto e cabelo não estão associados.
- Stills anteriores foram retirados para Assets/_catalog e Assets/174/legacy-options. Referências estão em Assets/174/references. Não são seleções aprovadas para a nova montagem.
- Pesquisas e evidências compartilhadas foram realocadas para Edit/_editor/research/migration-20261013. São arquivos históricos, não jobs ativos; scripts experimentais antigos com paths absolutos não são interface operacional atual.
- Cache legado de render/staging está em Cache/migration-20261013. Novas operações usam Cache/staging, Cache/render-public e Cache/<id>.
- Runtimes preservados como software: .runtime/processors (voz congelada), .runtime/hair (Python, código e pesos MatAnyone 2), .runtime/models (Whisper). Rosto Natural continua no repositório próprio.
- Pastas antigas analysis, public, jobs, library, references, reviews, out e .cache foram retiradas do editor. Sobrou apenas software, configuração e documentação; handoffs são documentação do fluxo.
- Registros da operação em Edit/_editor/migrations. Duas tentativas de rename de diretório foram revertidas; a migração concluída usa arquivos individuais com conferência de identidade no mesmo volume. Não houve exclusão de originais.

## Comportamento do harness

`studio.py paths` mostra as raízes efetivas. `EDITOR_STORAGE_CONFIG` permite configuração alternativa explícita, usada por fixtures isoladas. IDs e hashes continuam independentes dos nomes dos arquivos.

- `init ID`: cria Edit/ID/project.
- `register --kind still/font`: cópia persistente por hash em Assets/_catalog; `sfx` usa SoundFx/_catalog. Originais permanecem no local recebido.
- `render ID`: prévia em Edit/ID/reviews/<execução>/preview.mp4.
- `render ID --master`: candidato em Edit/ID/candidates/<execução>/master.mov, sujeito aos gates.
- `release`: verifica arquivo/aprovações e copia o master exato para Prontos/ID/<revisão>-<hash>/, sem sidecars e sem sobrescrita.
- `compile ID`: manifesto temporário em Cache/ID. Mídias preparadas ficam no staging externo.
- Voz Neural: WAV tratado e relatório em Edit/ID/audio/<execução>.
- `face-base`, `hair-prepare` e `hair-render`: sem --work, escolhem nova execução em Edit/ID/face ou hair; comandos seguintes recebem o path retornado.
- `attach-finish` e `hair-attach`: recusam associar acabamento em Cache. Saída associada é material preservado.
- `--out` não permite escrever mídias dentro do editor, em Source, nem em Prontos antes de release. O renderer legado foi desativado; usar studio.py.

## Retenção e limites

Cache pode ser recriado; resultados associados e evidências não são cache. A limpeza automática abaixo remove apenas cópias temporárias pertencentes à própria execução de renderização. A pesquisa histórica preservada não é uma lista de arquivos autorizados para exclusão.

A migração de diretórios foi testada com colisão e falha/rollback em fixtures. Reconexão por hash, registro externo, publicação de release em destino isolado, criação de projeto e bloqueio de master pendente têm testes. Há ainda prova real com fixture sintética de áudio neural, preparação facial e render H.264; ver o relatório de migração para os resultados finais. Esses testes não constituem aprovação de conteúdo de um vídeo real.

## Preservação no handoff para Premiere

Guardar projeto `.prproj`, versões/auto-saves necessários, XML de entrada, mídias, fontes/modelos gráficos usados e evidências em destinos externos sob Edit/Assets conforme a categoria. Usar um destino identificado por versão em `Edit/<id>/interchange/`; preservar os paths existentes do 174. Não guardar dependência editorial apenas em cache temporário de MOGRT.

Registrar no handoff o projeto/seqüência ativo, versão de entrada, arquivos/hashes e a decisão de Lucas. Após a passagem, JSON/XML de entrada são histórico de preparação, não comandos para sobrescrever a montagem. Antes de atualizar, ler a versão atual do Premiere e preservar alterações não salvas. Backups devem incluir `.prproj` e dependências; XML sozinho não preserva tudo. A atualização de fluxo não promove exports a Prontos nem libera limpeza.


## Higiene automática — autorização de Lucas em 15/10/2026

Implementada em `scripts/render_cache.py`, usada por `studio.py render` (prévia e master) e `sample_styles.py`:

- Cada render cria seu próprio diretório em `Cache/render-public/render-*`.
- Ao terminar o processo de renderização, suas cópias temporárias são removidas automaticamente, tanto em sucesso quanto em erro ou interrupção Python/Ctrl+C. A limpeza acontece também quando a cópia de preparação falha.
- A limpeza nunca percorre outras execuções, nunca apaga o staging compartilhado e não remove fontes, previews entregues, relatórios ou masters. A renderização seguinte refaz somente as cópias necessárias.
- Encerramento forçado (SIGKILL), queda do computador ou falha de permissão podem deixar resíduos. Não apagar essas pastas por idade: confirmar que não há render em execução e conferir fontes/dependências antes de remover.
- Em cada retomada e antes de processamento pesado, conferir espaço livre. Se houver pressão de espaço, priorizar resíduos comprovados de `render-public`; avisar quando a recuperação exigir arquivar material editorial. Não prometer limpeza automática de todo o disco.
- Não limpar automaticamente `Edit`, `Assets`, `Source`, `Prontos`, runtimes/modelos, CloudKit, recortes, imagens geradas, máscaras, voz/cabelo/maquiagem, backups do Premiere nem evidências. Arquivo antigo ou substituído não é automaticamente descartável.

A autorização cobre higiene de temporários regeneráveis; não autoriza remover material editorial. Nenhuma tarefa agendada foi instalada: a limpeza acompanha as renderizações. Para novos produtores de temporários, usar o mesmo contexto de execução ou implementar contrato equivalente antes de produção. Testes em `tests/test_render_cache.py` verificam sucesso, erro, interrupção, concorrência de diretórios e preservação de arquivos externos.


## Limpeza ao declarar vídeo finalizado — padrão confirmado em 17/10/2026

Quando Lucas disser que um vídeo foi finalizado, executar a limpeza desse vídeo sem pedir nova autorização: apagar caches, previews e intermediários sem uso, inclusive análises, frames, máscaras de processamento e versões intermediárias de cabelo, maquiagem, áudio e color grading. Manter as bases finalizadas com os tratamentos e a cor aplicados e somente os materiais necessários para reabrir e editar a montagem no Premiere, além dos arquivos finais de entrega. A declaração de finalização é o gatilho desta rotina; não depende dos gates legados do harness.

Antes de excluir, identificar o `.prproj` final e conferir suas dependências reais, incluindo caminhos relativos, links simbólicos e seus destinos. Preservar projetos, mídias de cena com as margens usadas, áudios, imagens/PSDs, máscaras editoriais, fontes, modelos gráficos e demais dependências efetivamente necessárias. Não confundir máscaras intermediárias de processamento de cabelo/maquiagem com máscaras editáveis usadas na montagem. Conferir referências de outros projetos e autosaves para não quebrar materiais compartilhados. Não reter intermediários apenas porque foram associados, examinados ou aprovados durante a preparação: a montagem final do Premiere rege a retenção após a declaração de finalização.

Confirmar que não há processamento usando os alvos e preservar alterações não salvas. Se o Premiere estiver fechado, inspecionar os projetos salvos; se houver estado não salvo que não possa ser conferido, limpar apenas o que já estiver comprovadamente sem uso. Não apagar originais brutos, bibliotecas compartilhadas, software ou modelos por inferência. Não seguir links para apagar suas fontes. Registrar arquivos removidos e volume, conferir a integridade dos projetos e das mídias finais preservadas e informar o resultado. Registros pequenos da limpeza podem permanecer.

Esta autorização substitui, para vídeos declarados finalizados, as restrições anteriores de retenção de previews e intermediários associados ou aprovados que não sejam necessários no Premiere. É uma rotina operacional do agente acionada pela declaração de Lucas, não um serviço ou agendamento instalado.
