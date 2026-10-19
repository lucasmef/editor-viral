# Revisão de privacidade do Git

Revisão inicial em 19/10/2026, antes do primeiro commit.

## Resultado e escopo

A revisão dos arquivos candidatos ao versionamento não encontrou padrões de credenciais conhecidas, chaves privadas, e-mails pessoais ou CPF. Foram verificadas atribuições de senha/token, URLs e referências a arquivos locais. Isto é uma varredura por padrões com revisão dos achados, não uma garantia de ausência de todo dado sensível.

Persistem nomes próprios, decisões editoriais e caminhos locais em documentos e defaults de conectores herdados. São metadados pessoais e operacionais, embora não sejam credenciais. Na revisão inicial, a recomendação foi manter o repositório privado. Após revisão adicional do histórico e dos artefatos versionados, Lucas autorizou explicitamente a publicação do código em 19/10/2026. Os caminhos locais e nomes herdados continuam sendo referências de desenvolvimento; gravações, configurações reais e relatórios de produção permanecem fora do Git.

## Proteções aplicadas

- `studio/storage.json` permanece local e ignorado. O Git oferece `studio/storage.example.json` com caminhos fictícios.
- Ambientes Python, dependências, modelos, caches, binários locais e logs ficam fora do Git.
- Arquivos `.env`, chaves e formatos comuns de mídia/projetos são ignorados.
- Relatórios históricos de execução, cópia, migração e auditoria ficam locais.
- O teste real herdado que aponta para mídia do editor de moda fica fora do Git e não foi executado.
- O template MOGRT herdado contém previews de mídia e foi excluído do versionamento junto de sua aprovação histórica. Ambos permanecem locais.
- O autor dos commits usa o endereço noreply associado à conta GitHub, sem expor e-mail pessoal.

Nenhuma gravação externa, catálogo de produção ou autorização de limpeza foi importada. Os arquivos excluídos não foram apagados. O `.gitignore` previne inclusão acidental comum, mas não substitui a revisão de cada commit.

## Validação inicial

`pnpm check` passou e `pnpm test:harness` passou com 224 testes. Esses testes validam software e fixtures, não aprovam qualquer vídeo.

O clone não inclui runtimes, configuração real, template MOGRT ou aprovações. Recursos que dependem deles exigem preparação local; não criar aprovações fictícias para contornar gates.
