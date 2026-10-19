# Studio como etapa de revisão manual

> HISTÓRICO — desde 15/10/2026, Lucas não quer usar Remotion Studio para revisão/ajustes finais. Ver [fluxo vigente](FLUXO_EDICAO_PREMIERE.md). Preservar esta implementação, sessões e ajustes do 174; instruções abaixo descrevem a direção anterior, não autorizam reabrir, regenerar ou migrar sessões.

Direção de Lucas, 14/10/2026: o agente prepara o vídeo e Lucas faz os ajustes finais no Remotion Studio. Não entregar uma interface que aceite edições na prévia, mas descarte essas edições ao salvar, reabrir ou renderizar. A análise abaixo identifica o estado atual; não certifica recursos ainda não implementados.

## Diagnóstico anterior à correção (histórico)

- Pacotes instalados `remotion`, `@remotion/cli` e `@remotion/renderer`: 4.0.534, alinhados. Não há indicação de que reinstalação resolva o problema de crop.
- O Studio edita o código TSX da sessão. Nosso projeto oficial é JSON externo. `scripts/look_studio.py` criou uma ponte parcial entre os dois, não uma integração completa de edição.
- `scripts/studio_geometry.cjs` extrai apenas translate e escala uniforme e calcula uma assinatura de todo o restante do código. Qualquer outra alteração é recusada, inclusive controles que a interface nativa oferece normalmente.
- Caso real: `cropTop={0.11}` em `cena-1-cena-01-girl-top-saia-v05-sob-casaco`. A assinatura da sessão difere da inicial; retirando somente esse atributo para comparação em arquivo temporário, ela volta a coincidir. Não foi removido da sessão real. Portanto o Studio gravou o crop; o sincronizador impediu sua persistência no JSON oficial.
- Também existem duas posições editadas no top/saia feminino (estado antes e sob casaco). Não regenerar a sessão a partir do JSON antes de recuperar as alterações nativas.
- Snapshot de recuperação preservado em `Edit/174/project/history/20261014-studio-native-edits-recovery/`, com TSX e manifesto compilado de origem. É evidência/recuperação, não outra fonte editável. O crop ainda NÃO foi importado no projeto oficial.
- Os 156 testes anteriores verificaram o contrato existente. Não provaram compatibilidade com todos os controles do Studio. O teste de interface anterior cobriu mover, escala e desfazer; faltou testar crop e os demais controles oferecidos.

## Lacunas

| Operação | Situação observada no código | Trabalho necessário |
|---|---|---|
| Mover e escala proporcional dos looks | Importação implementada | Manter e testar também após reabrir e na saída oficial |
| Crop nativo | TSX aceita; ponte rejeita | Persistir crop visual separado do crop de extração da imagem; reproduzir exatamente a semântica nativa, sem alterar textura/escala/posição por engano |
| Rotação, origem, escala por eixo e opacidade | Ponte rejeita | Campos persistentes, validação e mesma ordem de transformações no editor e renderer |
| Tempos de entrada/saída dos looks | Ponte rejeita | Mapear frame global/local e âncoras, definir override manual sem o compilador desfazê-lo |
| Duplicar, excluir e ordenar camadas | Lista fixa e assinatura impedem | Identidades estáveis, ordem de composição, histórico e atualização das referências aos looks |
| Keyframes e efeitos | Expressões não importadas | Contrato de animação/efeitos e mesma interpretação na saída; não avaliar TSX arbitrário para contornar validação |
| Legendas, girl/boy e base gravada | Fora dos alvos editáveis preparados | Componentes interativos e persistência no documento correto (estilo, timeline ou acabamento) |
| Desfazer, reabrir e recuperar | Cobertura parcial | Histórico durável de todas as propriedades, recuperação de sessão pendente e avisos claros de conflito |
| Render do Studio | Sessão contém proxy e aviso de salvamento | Separar interface da composição exportável; saída oficial precisa ler as edições e usar mídias de produção |

## Arquitetura a ajustar

Preservar o projeto externo como única fonte oficial, conforme AGENTS.md. Usar os componentes/esquemas interativos oficiais para declarar os controles suportados, em vez de expor um contêiner genérico com controles sem persistência. Expandir o contrato editável e seu renderer em conjunto: toda propriedade editada precisa sobreviver ao ciclo Studio → projeto → Studio → render oficial.

O código gerado pode continuar como representação de edição, mas nunca como cache descartável enquanto houver ajustes não importados. Salvar snapshots pendentes fora do cache, registrar alterações por peça/propriedade, preservar valores não alterados e comunicar exatamente qual campo não foi importado. Uma alteração não suportada não pode ser confundida com sucesso nem com perda silenciosa de outros ajustes.

Não resolver removendo a assinatura de proteção ou aceitando qualquer TSX: isso deixaria mudanças visíveis no Studio sem equivalente na exportação. Tampouco substituir o projeto JSON por TSX independente sem migrar catálogo, checkpoints, acabamentos e exportação: criaria duas timelines concorrentes.

Ordem de implementação: (1) recuperar o crop existente e suportar transformações estáticas dos looks; (2) controles de títulos/legendas/base e tempos das peças; (3) operações estruturais, animações e efeitos conforme os controles nativos utilizados. Não anunciar compatibilidade completa antes de verificar cada grupo. Os controles de uma etapa incompleta precisam ficar desabilitados ou claramente identificados antes da edição, e não apenas apresentar erro depois.

## Critérios de aceitação

Para cada operação: editar pela interface, conferir persistência oficial, reabrir uma sessão a partir do projeto, renderizar pelo harness, comparar a geometria/aparência com a edição e desfazer/refazer sem afetar outras peças. Incluir casos com crop preexistente de extração, máscaras de jaqueta, mudança de origem, acessórios, múltipla seleção, limites da cena e conflito externo. Preservar 4K tratado, áudio, guias e regras de aprovação; teste técnico não aprova visualmente o vídeo.

## Organização futura das cenas

Lucas pediu que, nos próximos projetos, a sequência principal mostre as cenas uma após a outra, com cortes e tempos coerentes, evitando uma fileira independente para cada cena. Os looks continuam precisando de camadas sobrepostas, mas devem ficar organizados por cena/grupo, com nomes legíveis e possibilidade de recolher grupos quando suportado. A composição temporal atual já é sequencial; a solicitação é também de apresentação da timeline. Não reorganizar as camadas do 174 nesta análise: Lucas deixou explicitamente essa mudança para depois.

Referências oficiais consultadas: https://www.remotion.dev/docs/studio/interactivity e https://www.remotion.dev/docs/studio/interactivity-best-practices. A interatividade escreve alterações no código; a persistência em nosso formato externo é responsabilidade da integração.


## Correção implementada em 14/10/2026

O importador de geometria foi substituído na sessão ativa por persistência de propriedades nativas por peça (`native.props`). Crop, transformações, opacidade, estilos e controles de tempo usam o mesmo componente nativo na prévia e no renderer. Duplicação/exclusão têm identidades e atualização dos grupos; undo recupera a fonte imutável da sessão. Expressões de interpolação/keyframes são serializadas como dados e interpretadas por uma lista de operações conhecidas, sem eval. A formatação do Studio é normalizada antes de conferir a origem da imagem.

O crop real de 11% do top/saia sob a jaqueta da cena 1 foi importado no projeto oficial, junto com os deslocamentos existentes. Sua cópia histórica permanece preservada. Testes de interface alteraram crop e rotação e desfizeram os testes. Uma nova sessão foi compilada a partir do projeto salvo. Prévia completa exportada pelo harness em `Edit/174/reviews/studio-native-v1/174-native-preview.mp4`; comparação visual no frame 230, com guias e crop. Não constitui aprovação criativa.

Limite explícito: a correção cobre os controles das peças existentes; não migra a edição da apresentadora, legendas/títulos, nem introduz suporte a novos elementos, HTML-in-canvas, motion blur ou pre-compose. Essas alterações estruturais são rejeitadas, não ignoradas. O plano para esses recursos permanece em aberto. Não declarar “todos os recursos do Remotion funcionam”.
