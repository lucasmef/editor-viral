# Estado do editor-viral — 19/10/2026

Pedido de Lucas: criar cópia independente do editor, com este nome, para vídeos digitais; avaliar skills externas e integrar o raciocínio de marketing do Oliveto. O fluxo atual de moda permanece intacto.

## Decisão tecnológica

Manter Remotion 4.0.534, React e o fluxo de transferência/finalização pelo Premiere. A documentação atual do Remotion apresenta captions, effects, transitions, Player e múltiplos caminhos de renderização; HyperFrames usa HTML e animações com GSAP. São alternativas de geração por código. Não foi realizado benchmark equivalente: não afirmar superioridade de velocidade/qualidade ou que um é mais avançado em tudo. Para esta base, manter Remotion reaproveita código e integrações existentes. Reavaliar HyperFrames só diante de necessidade concreta demonstrada em piloto isolado.

Fontes primárias consultadas:
- https://github.com/remotion-dev/remotion
- https://github.com/heygen-com/hyperframes
- https://hyperframes.app/docs/1-startup/1-introduction

## Avaliação das skills externas

Leitura documental, sem instalação ou execução de seus scripts. São referências, não novas autoridades do projeto. Foi escrita uma skill própria, sem redistribuição integral dos textos externos.

- [Vertical Video Editing](https://github.com/adriiita/vertical-video-editing-skill/blob/main/skills/video-editing/SKILL.md): consultadas entrada, fluxo, gramática editorial e requisitos. Começa com roteiro aprovado. Aproveitar mapa de decisões por trecho, ritmo guiado pela fala, movimentos suaves e destaques. Não adotar engine obrigatória, split como padrão, abertura sempre animada, cortes mínimos prescritos, preset ou áudio único achatado. Não resolve sozinha transcrição/reconstrução de gravação longa.
- [Caption Animation](https://github.com/iart-ai/tiktok-video-skills/blob/main/skills/caption-animation/SKILL.md): consultados contrato e timing por palavra. Aproveitar sincronismo e legibilidade; adaptar aparência e duração por vídeo. Não instalar o pacote para presumir que suas animações passam como texto editável ao Premiere.
- [Viral Clip Editor](https://github.com/eligapris/viral-clip-editor-skill/blob/main/SKILL.md): consultada descrição/pipeline de transcrição, seleção, crop, corte e captions. Útil como referência de extração; análise não certifica qualidade perceptiva nem implementação de reordenação semântica no nosso projeto.

## Oliveto e divisão de trabalho

Disponível na sessão de origem como gepeto (nome legado), versão consultada 1.3.3. Foram lidos skillmaster, regras operacionais, índice de contexto, social (ganchos e reaproveitamento), referência Short-Form Video e marketing-psychology (orientação de aplicação, hipóteses e princípios pertinentes). Não foi necessário consultar contexto de campanha ou alterar o plugin global para criar esta infraestrutura.

Oliveto já ajuda a encontrar ideias, ganchos, benefício, ordem e fechamento. A skill local conecta isso à edição: transcrição temporizada, origem de cada corte, comparação da ordem original/proposta, preservação de sentido, reservas A/V e remapeamento após reordenação. Não foi preciso modificar o Oliveto. No novo chat conferir disponibilidade pelo catálogo; plugin disponível neste chat não comprova ativação em outro.

## O que está pronto e o que falta

Pronto: cópia independente de software/runtimes/dependências; caminhos externos novos; skill de direção narrativa; instruções próprias; pesquisa e prompt de continuidade. Templates e código de origem foram preservados para reaproveitamento, sem aprovações herdadas de vídeos.

Na preparação inicial, ficaram pendentes o primeiro material, o modo sem looks e a validação real. Continuação em 19/10: Lucas forneceu IMG_5144.MOV como piloto sem roteiro. O comando `init --mode no-looks` cria estilo neutro, sem títulos girl/boy, sem legenda contínua imposta e sem ativar acabamento de voz herdado. Os gates dispensam looks e stills ausentes somente nesse modo; overlays existentes, cortes, legendas, imagem, áudio e aprovação do arquivo exato continuam sujeitos a revisão. Mudança de modo invalida aprovação de corte. Fixtures cobrem esses limites.

Pendente: conferência auditiva e aprovação do corte do piloto; objetivo/público/canal final confirmados; teste de zoom e novas legendas até o Premiere; validação audiovisual ponta a ponta. A conexão CEP não respondeu ao teste somente de leitura nesta sessão. Nenhuma transferência real nem aprovação final foi registrada. As melhorias de transferência aguardam validação em projeto separado, nunca no 177.

### Piloto sem aprovação prévia do corte — orientação posterior de Lucas

Lucas pediu explicitamente que o vídeo de teste fosse entregue com acabamento, legendas e motion antes de aprovar o corte. Essa exceção autoriza produzir o piloto; não equivale a aprovação do arquivo nem liberação em Prontos. A entrada `src/digital.tsx`, composição `DigitalPilot`, implementa legendas em grupos com palavra ativa, cartões animados e zooms por intervalos. Os parâmetros ficam no projeto externo, junto dos tempos de origem e dos relatórios. A voz original é montada separadamente, com fades de 5 ms nas bordas, tratamento leve e normalização; nenhum trecho de fala é sintetizado.

Nesta máquina o Chrome Headless Shell herdado travou em callbacks de quadro e decode de imagem. A amostra renderizou com `--chrome-mode=chrome-for-testing`, mantendo Remotion 4.0.534; não foi necessário alterar dependências ou o navegador global. Renderização do piloto usa essa opção e `--scale=0.5` para 540×960. O caminho ao Premiere continua pendente de teste real, e efeitos da composição digital não estão certificados como transferíveis.

O segundo ASR (Whisper large-v3-turbo em MLX) foi baixado para Cache/models e executado localmente. A transcrição original, passagens locais, alinhamentos e a transcrição da montagem são evidências automáticas; não registrar escuta humana. Guardar a distinção no relatório mesmo quando a transcrição da montagem preservar a fala.

Os documentos herdados docs/EDITOR_OPERACAO_ATUAL.md, docs/HARNESS.md e docs/ARMAZENAMENTO.md descrevem a origem. Para paths vale studio/storage.json; para decisões editoriais valem este documento, AGENTS.md e a skill local. Exemplos de 174/177/101 não são jobs deste editor. Não executar scripts de teste real da origem contra mídia de moda.

## Armazenamento e operação

Todas as seis raízes ficam sob /Users/lucas/Movies/EditorViral: Assets, Edit, Source, SoundFx, Prontos e Cache. Não foram copiados brutos, vídeos finalizados, catálogo nem caches de produção. Prontos é local neste projeto; nenhuma sincronização em nuvem foi configurada.

Os runtimes Python/Node foram copiados como arquivos independentes via clone APFS; executáveis de ambiente podem depender das instalações globais já existentes. Não há symlink de pasta para o editor original. Conectores ainda usam motores locais externos (como rosto-natural); isso não implica mídia compartilhada ou serviço novo. Porta opcional do Remotion Studio: 3175; Studio não substitui revisão pelo fluxo acordado.

Comandos de software: pnpm check; pnpm test:harness. Com um job real: pnpm status ID; pnpm validate:final ID. Sem vídeo criado, não executar gates com ID de moda nem produzir uma aprovação fictícia.
