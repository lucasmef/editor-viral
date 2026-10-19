# Editor Viral

Transforme gravações em cortes com uma história clara, preservando a origem de cada trecho e o controle sobre a montagem.

Editor Viral é uma base local de edição para vídeos digitais: combina direção narrativa com apoio do Oliveto, composição em Remotion e um caminho de transferência para o Adobe Premiere Pro. O nome expressa a proposta editorial; não promete alcance ou viralização.

## O que já existe

- **Montagem rastreável:** estrutura de projetos, seleção de tomadas, tempos de origem e revisão de cortes.
- **Vídeos sem looks:** modo `no-looks`, com estilo neutro e gates adaptados, sem aprovações fictícias de moda.
- **Composição digital:** legendas em grupos com palavra ativa, cartões animados e zooms por intervalo na composição `DigitalPilot`.
- **Revisão e entrega:** validações de mídia, margens de áudio e vídeo e aprovação vinculada ao arquivo final.
- **Caminho ao Premiere:** scripts e integração para transferência e conferência. Depois da transferência, o Premiere é a fonte da montagem.

**Estado:** desenvolvimento com piloto em validação. A transferência dos efeitos digitais e o fluxo audiovisual completo ainda precisam de teste real. Uma renderização não equivale a aprovação do corte ou do arquivo final.

## Começar

Leia [estado e decisões](docs/EDITOR_VIRAL.md), [instruções do projeto](AGENTS.md) e [skill editorial](skills/editor-viral/SKILL.md).

O projeto usa Node.js, pnpm, Python e FFmpeg. Remotion está fixado em **4.0.534**. Ambientes Python, modelos e motores opcionais são locais e não acompanham o Git; o clone sozinho não reproduz a instalação desta máquina.

```sh
pnpm install --frozen-lockfile
cp studio/storage.example.json studio/storage.json
```

Antes de executar, substitua todos os caminhos do exemplo por diretórios absolutos exclusivos deste editor. As seis raízes são `assets`, `edit`, `source`, `soundfx`, `ready` e `cache`. Não aponte para o editor de moda. A configuração real fica ignorada pelo Git.

Com o armazenamento configurado e os runtimes disponíveis:

```sh
pnpm check
pnpm test:harness
pnpm studio
```

O Studio usa a porta **3175**. Os comandos Python em `package.json` dependem de `.venv/` e `.runtime/hair/venv/` já preparados. Veja [integrações](docs/INTEGRACOES.md) e [harness](docs/HARNESS.md) para o contexto técnico herdado; caminhos e decisões atuais seguem `studio/storage.json` e `docs/EDITOR_VIRAL.md`.

Com um job real, consulte e valide usando seu identificador:

```sh
pnpm status ID
pnpm validate:final ID
```

Sem as aprovações exigidas, a entrega deve permanecer bloqueada.

## Fluxo editorial

1. Preservar o bruto e registrar SHA-256, resolução e margens reais de áudio e vídeo.
2. Indexar a fala e propor trechos com referências temporais da gravação. ASR ajuda a localizar conteúdo; não comprova escuta.
3. Comparar tomadas e revisar a ordem proposta, preservando o sentido e o roteiro aprovado.
4. Após a aprovação do corte, aplicar acabamento e remapear os tempos quando houver reordenação.
5. Conferir a transferência ao Premiere e revisar separadamente o arquivo final.

Exceções autorizadas para um piloto não são aprovações reutilizáveis em outros vídeos.

## Estrutura

| Pasta | Conteúdo |
| --- | --- |
| `src/` | Composições Remotion, tipos e interface |
| `scripts/` | Edição, armazenamento, revisão, validação e transferência |
| `studio/` | Estilos, templates e exemplo de armazenamento |
| `tests/` | Fixtures e testes do harness |
| `integrations/` | Patches da integração Premiere |
| `skills/editor-viral/` | Direção narrativa e regras editoriais |
| `docs/` | Decisões, operação e referências técnicas |

## Privacidade e separação dos projetos

O Git contém software e documentação. Brutos, projetos de vídeo, relatórios de produção, modelos, caches e credenciais devem ficar fora do versionamento. Veja a [revisão de privacidade](docs/PRIVACIDADE_GIT.md).

A base foi derivada de um editor de moda. Presets, exemplos e conectores herdados são referências técnicas, não direção editorial automática. O editor de origem e seus vídeos permanecem independentes; não executar jobs antigos nem reutilizar suas aprovações.
