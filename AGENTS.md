# Editor Viral

Projeto independente criado a pedido de Lucas em 19/10/2026, a partir de editor.
Ler docs/EDITOR_VIRAL.md e skills/editor-viral/SKILL.md antes de editar vídeos.

- O editor de moda em ../editor e seus vídeos 174/177 ficam intocados. Não executar seus jobs nem copiar seus registros de aprovação.
- Código, runtimes e testes foram copiados; mídia e catálogo começam vazios. studio/storage.json aponta exclusivamente para /Users/lucas/Movies/EditorViral. Não usar EDITOR_STORAGE_CONFIG de outra sessão sem conferir os destinos.
- Software nesta pasta; mídia, projetos e relatórios de vídeos nas raízes externas. Um único projeto editável por vídeo. Após transferência, Premiere é a fonte da montagem.
- Manter Remotion 4.0.534 e o caminho de transferência ao Premiere. Não instalar HyperFrames por inferência nem migrar o editor de moda.
- Oliveto está disponível nesta sessão como gepeto. Consultar as skills atuais pelo catálogo, sem editar o cache do plugin. Social é principal para ganchos/roteiros/reaproveitamento; marketing-psychology é apoio; copywriting/copy-editing conforme a entrega.
- A skill local acrescenta decisão narrativa com origem temporal verificável. Instruções editoriais antigas sobre looks, 101, girl/boy, legenda contínua e vídeos numerados são referências da origem, não direção automática deste projeto.
- O código herdado ainda contém presets e gates de moda. Não marcar looks/aprovações fictícios para passar gates. Adaptar explicitamente o modo sem looks em uma mudança testada quando o primeiro vídeo exigir; a criação desta cópia não implementou esse modo.
- Preservar originais, SHA-256, resolução, margens reais A/V e fontes recuperáveis. Tratar após aprovação do corte; remapear tempos depois de reordenar. ASR é índice, não prova de escuta.
- Galeria de tomadas quando houver alternativas; para vídeo longo, apresentar trechos e ordem proposta com referências de origem. Respeitar roteiro/ordem já aprovados. Revisão do corte e do arquivo final continuam separadas.
- Não usar scripts/test_face_connector_real.py: é uma referência herdada que aponta para mídia do editor de moda. Fixtures e testes unitários são o caminho inicial.
- Conferir espaço antes de processamento pesado. Não limpar mídia por idade ou importar autorizações históricas de limpeza. Não publicar nem enviar gravações a serviços novos por inferência.
- Rodar pnpm check e pnpm test:harness após alterações de software. pnpm status ID e pnpm validate:final ID exigem um job real; ausência de aprovação deve continuar bloqueando a entrega.
