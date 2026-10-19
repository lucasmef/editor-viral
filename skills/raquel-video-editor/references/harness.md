# Harness v2 no projeto editor

Direção vigente de 15/10/2026: ler [preparação e Premiere](../../../docs/FLUXO_EDICAO_PREMIERE.md). Os comandos abaixo continuam disponíveis para preparação; após handoff registrado, a montagem é regida pelo `.prproj`. Remotion Studio é histórico, sem migração automática do 174.

Fonte de verdade operacional: `/Users/lucas/Documents/Codex/editor/docs/HARNESS.md`. Ler esse documento para comandos, contratos, revisão, arquivamento e retomada; não duplicar instruções detalhadas aqui.

Entrada: `.venv/bin/python scripts/studio.py`. Projetos em `Edit/<id>/project/`, mídias em `Edit/_editor/media.json`. Os JSONs editáveis geram o manifesto consumido pelo Remotion. O 174 foi reiniciado por Lucas; src/empty-project.json é só a tela inicial vazia do renderer. Raízes oficiais em studio/storage.json.

`status` informa etapas/fingerprints/mídias; `overview` regenera STATUS.md; `checkpoint` salva versão; `fork` retoma em outro job; `assemble` mescla cenas de revisões fixadas; `relink` confere SHA-256. Não inferir backup a partir de caminho de nuvem e não apagar originais.

`approve` registra uma aprovação realmente dada, com evidência e escopo. `render --master` gera candidato tecnicamente verificado somente após checkpoints válidos. `release` exige aprovação e playback real do arquivo exato. Código não substitui escuta, percepção de gesto ou julgamento de styling.

Mudança de corte invalida revisões dependentes; áudio tratado fica vinculado à montagem. Stills são persistentes, não caches descartáveis. Quadros inteiros e intervalos semiabertos usam o fps do projeto. Âncora de gesto/fala é local à cena. PNG com alpha não garante recorte limpo; inspecionar sobre vídeo real.

Integrações catalogadas e seus limites: `docs/INTEGRACOES.md`. Não afirmar execução de Rosto Natural/Voz Neural apenas porque README ou testes históricos descrevem resultados.
