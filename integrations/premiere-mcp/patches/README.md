# premiere-pro-mcp 1.24.0 + local safe-move-v1

Correção local autorizada por Lucas em 15/10/2026, no servidor existente de leancoderkavy. Não cria outro MCP, não troca dependências nem altera o conector CEP assinado.

## Falha e correção

A implementação original mudava a faixa no tempo antigo e só depois mudava o tempo. QE podia sobrescrever vizinhos nesse ponto intermediário, e o handler verificava apenas o clipe movido.

Quando `new_track_index` é informado, o handler passa a usar `safeMoveScript`:

1. Recusa destino final ocupado, origem/destino bloqueados ou com transições; recusa clipe movido com keyframes ou parceiros vinculados.
2. Escolhe tempo antes da faixa, faixa antes do tempo, ou uma faixa existente livre no intervalo percorrido. Confere também o intervalo percorrido pelas escritas de bordas. Não cria faixa automaticamente. Sem rota segura, retorna `not_applied`, `timelineChanged:false`.
3. Fotografa IDs, faixa, nome, origem, in/out, início/fim, enabled, velocidade/direção e valores de componentes/keyframes legíveis de todos os clipes A/V. Limites: 500 clipes, 10.000 propriedades/keyframes.
4. Compara a sequência depois de cada passo. Divergência retorna `committed_unverified`, nunca sucesso. Não faz rollback cego. Usar a recuperação própria do MCP e conferir o estado antes de continuar.

Chamadas sem `new_track_index` mantêm o código upstream. QE é não documentado; a prova cobre Premiere 26.5.2 e as fixtures usadas, não qualquer versão ou estrutura de projeto. Legendas, máscaras e outros dados não enumeráveis não são certificados genericamente pela fotografia de propriedades. A comparação integral da exportação também cobriu a aparência das legendas existentes neste teste.

## Aplicar / restaurar

`python3 integrations/premiere-mcp/patches/apply.py` aplica de forma idempotente somente sobre o original de checksum conhecido ou a própria versão corrigida. Recusa outra versão/modificação.

`python3 integrations/premiere-mcp/patches/apply.py --restore` restaura o handler original, reintroduzindo sua limitação. Não usar para edição entre faixas sem avaliação.

Recarregar a conexão `premiere_pro` se ela já estiver em execução. A configuração e o caminho do servidor continuam os mesmos; os clientes stdio de validação já iniciaram com o código corrigido. Atualizações/reinstalações do pacote podem substituir o patch: não reaplicar sobre versão diferente sem revisão.

Código instalado: `.runtime/premiere-pro-mcp-1.24.0/package/dist/tools/timeline.js` e `safe-move-script.js`. O fonte upstream instalado contém JS compilado; `timeline.js.map` continua sendo do upstream e não representa a inserção local.

## Testes

`node --test integrations/premiere-mcp/patches/safe-move.test.mjs`: 10 testes. Reproduzem a sobrescrita antiga, três rotas, recusa de colisões/falta de rota/links/animação/bloqueio/transição, e detecção de alteração colateral.

No Premiere: 11 comparações completas durante movimentos de PNG, vídeo, MOGRT e áudio, mais comparação após salvar/fechar/reabrir. Os dez clipes e seus valores legíveis permaneceram iguais ao baseline, descontando somente tempo/faixa previstos de cada movimento. Inclui mover o PNG original com escala manual 93%, rotação 7° e Crop. Movimentos foram desfeitos por operações inversas validadas, não por reconstrução de clipes. Uma faixa V7 vazia permanece para permitir a rota intermediária.

Exportação após reabrir: 479/479 frames decodificados idênticos e PCM decodificado idêntico a `validacao-v3.mp4`. Sem necessidade de avaliação visual subjetiva para afirmar igualdade desses conteúdos. Não é aprovação estética do padrão 101.

Detalhes e evidências em `docs/PREMIERE_MCP.md` e na raiz externa de testes. `pnpm check` passou; 160 testes do harness passaram; status consultado; gate final continua bloqueado por checkpoints de produção, como esperado. Nenhum render/master de produção executado.
