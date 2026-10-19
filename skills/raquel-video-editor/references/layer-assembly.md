# Montagem por duplicação e máscara — demonstração de Lucas

Método explicado por Lucas em 15/10/2026 com cinco PSDs e capturas da montagem masculina da cena 4 do 174. Complementa [separação fiel](separation-prompt.md) e [produção de recortes](cutout-production.md). Esta documentação não autoriza editar arquivos, substituir mídias ou alterar a timeline existente.

## Planejar a necessidade pela ordem do vídeo

Primeiro posicionar o look completo original como gabarito e obter a aprovação de tamanho/localização. Depois assistir à cena para confirmar o que aparece primeiro, o que entra depois e o gesto/frame de cada entrada. Roteiro, ASR e cor das roupas ajudam a mapear, mas não substituem a conferência audiovisual. Registrar eventos locais da cena; não adivinhar novos tempos a partir de screenshots.

Neste exemplo: **jeans médio = jaqueta + calça**, depois **amarelo = camiseta + fone**; os tênis pertencem ao complemento lavanda. Esta combinação e essa ordem pertencem a este look, não a todos os vídeos.

A completude necessária depende da visibilidade em TODOS os estados:

- A base que aparece primeiro precisa funcionar sozinha: jaqueta com costas/forro inteiro, inclusive a área que depois ficará atrás da camiseta.
- Uma camiseta que só aparece sob a jaqueta pode conter apenas as partes necessárias para a abertura visível. **Não exigir nem gerar mangas escondidas.** Isso não é falha de recorte.
- Se outra montagem mostrar a camiseta sozinha, planejar uma versão completa, incluindo mangas. É uma necessidade daquele estado, não uma regra universal de toda camiseta.
- Se a ordem for alterada depois, revisar essas necessidades antes de reaproveitar as imagens: uma versão suficiente para ficar por baixo pode ser insuficiente sozinha.

## Ordem de construção demonstrada

1. **Gabarito:** inserir a foto original do look completo para definir proporção e posição. É referência de trabalho; ocultar/remover sua exibição no resultado final para que roupas/acessórios não apareçam antes da hora.
2. **Base:** inserir o PSD de jaqueta completa + calça, alinhado ao gabarito. Neste caso as peças entram juntas e conservam sua relação interna. O forro preenche a abertura inicial; não pode haver um buraco antes da entrada do amarelo.
3. **Camiseta:** inserir acima da base e alinhar à região original. Antes de aplicar a frente da jaqueta, ela pode cobrir visualmente as lapelas; isso é um estado de trabalho, não o acabamento final.
4. **Duplicar a instância da base já posicionada:** colocar essa cópia acima da camiseta. A cópia deve conservar posição, escala, rotação, âncora e registro da original; não adicionar uma nova jaqueta e tentar posicioná-la a olho. Nesse momento ela cobre a camiseta, o que é esperado antes da máscara.
5. **Frente da jaqueta:** na cópia, usar uma versão do MESMO PSD com máscara diferente. Remover a calça da camada superior e abrir somente a região necessária para revelar a camiseta; manter mangas, gola, lapelas, painéis frontais e suas bordas. A base completa permanece intacta por trás. Não gerar uma segunda jaqueta nem refazer cor, textura ou geometria.
6. **Fone:** inserir acima das camadas de roupa, na posição da referência. Camiseta e fone entram no evento amarelo confirmado no vídeo; a ordem de empilhamento não implica tempos de entrada diferentes.
7. **Tênis:** sobrepor calça + tênis à calça sem tênis, alinhar visualmente o conjunto e só então mascarar a calça superior com feather amplo na borda recortada da calça, conforme o procedimento abaixo. Manter a calça-base. Respeitar o evento próprio dos calçados; sua presença nas capturas de trabalho não aprova entrada antecipada.

Pilha final da região superior, de baixo para cima:

| Camada | Função |
|---|---|
| Base jaqueta completa + calça | Jeans inicial, costas/forro e calça preservados |
| Camiseta | Amarelo dentro da abertura da jaqueta |
| Cópia da base, máscara só da frente da jaqueta | Oclusão correta de laterais/mangas da camiseta, sem duplicar calça |
| Fone | Acessório em primeiro plano conforme referência |

Uma camada frontal idêntica à base nas regiões visíveis pode existir desde a entrada do jeans; ou entrar junto com a camiseta, desde que não provoque salto. Escolher conforme a timeline vigente, sem mudar cortes aprovados. Base, frente e camiseta devem coexistir durante todo o estado composto. Conferir o frame imediatamente anterior e posterior a cada entrada.

## Por que a duplicação mantém o encaixe

O par base/frente compartilha os mesmos pixels de origem, canvas e sistema de coordenadas; só a máscara muda. Ao duplicar a instância já posicionada e substituir sua fonte pela versão frontal compatível, a geometria não precisa ser reconstruída.

Preservar no par:

- Mesmas dimensões do documento, origem, resolução/densidade e convenção de importação.
- Mesmo ponto de ancoragem, posição, escala X/Y, rotação, espelhamento e crop/efeitos geométricos; conservar keyframes quando existentes.
- Mesma aparência dos pixels mantidos: sem color grading separado, transformações acumuladas ou segunda geração.
- Máscara não destrutiva sempre que disponível; preservar a versão completa e o arquivo frontal derivado.

**Não aparar a frente isoladamente até os limites da jaqueta.** Se a base inclui a calça, a frente pode manter a área inferior transparente do mesmo canvas. O espaço vazio é necessário ao registro desse par e não é desperdício que justifique perder o alinhamento. Essa exceção prevalece sobre a orientação genérica de deixar cada PNG/PSD justo ao conteúdo.

Para camiseta, fone e outros itens independentes, canvas ajustado ao conteúdo continua permitido, com âncoras/offsets registrados. O canvas comum do par é o do asset/PSD, não uma rasterização de toda a composição de vídeo.

Mesmo com dimensões iguais, conferir o resultado após substituir a fonte: a opção de importação de PSD (documento composto ou camada selecionada) pode usar limites distintos. Não assumir que uma substituição manteve origem/âncora sem observar. Se a integração não duplicar instâncias com fidelidade, registrar e reaplicar as transformações exatas pela operação disponível, sem recompor a olho.

## Tênis encaixados na calça — alinhamento visual e feather

Complemento confirmado por Lucas em 15/10/2026. Aplicar quando os tênis encostam/entram sob as barras; não impor esse método a calçados sem contato com a roupa.

1. Preparar duas imagens a partir da mesma referência: **calça sem tênis** e **calça + tênis**. Preservar perspectiva dos pés, dobras e contato com as barras; não gerar os tênis numa pose genérica isolada.
2. Colocar a calça sem tênis como base no vídeo. Sobrepor a imagem calça + tênis acima dela.
3. **Alinhar no olho antes de recortar:** ajustar o posicionamento do conjunto sobre a base, conferindo as duas pernas, costuras, barras e dobras. Se necessário, usar escala proporcional para compatibilizar os enquadramentos. Alternar a visibilidade ou reduzir temporariamente a opacidade ajuda a comparar; restaurar a opacidade antes de finalizar. Registrar a transformação obtida. Não presumir que os dois arquivos já coincidam só por virem do mesmo prompt.
4. Depois de alinhar, mascarar a calça da camada superior, conservando os tênis e uma faixa generosa de calça acima dos tênis para receber a transição esfumada. A calça principal permanece na base.
5. Aplicar **feather amplo e bem esfumado na borda da máscara dessa faixa inferior**, fundindo o trecho de contato com a calça-base. Ajustar visualmente no tamanho de uso; não fixar um número universal de pixels. Não desfocar a imagem inteira, as solas ou o contorno dos tênis. É suavização espacial da junção, não fade temporal da camada.
6. Conferir os dois pés e o frame anterior/posterior à entrada dos tênis: sem barra dupla, halo, transparência vazando ou salto visível de cor/textura. Conservar posição e máscara depois do encaixe; mover/escalar o look deve levar base e complemento juntos.

Diferença em relação à frente da jaqueta: ali o alinhamento vem da duplicação da MESMA imagem com o mesmo canvas; aqui há DOIS estados de imagem e Lucas confirma o alinhamento visual como parte normal da montagem. Não exigir coincidência automática nem rejeitar o par apenas por precisar de posicionamento. Esse ajuste não autoriza deformar pernas ou girar cada pé independentemente para esconder uma pose incompatível. Se os contatos das duas pernas não puderem coincidir, tratar a divergência do material sem deformar o conjunto; o feather amplo serve para fundir a borda da máscara, não para corrigir pose.

## PSD é um formato de trabalho válido

Lucas autorizou manter PSD. Preservar PSDs originais, camadas e máscaras; não exigir conversão para PNG, achatar o original ou regenerar a fotografia. Quando um consumidor exigir um derivado, criar uma cópia versionada com alpha e dimensões compatíveis, mantendo o PSD como fonte. A importação no Premiere deve registrar a opção usada e ser conferida; este documento não certifica suporte MCP a todas as propriedades internas de PSD.

## Conferência e evidência deste exemplo

As capturas enviadas mostram a progressão do gabarito completo, base jeans, camiseta por cima, frente da jaqueta recomposta e fone. Demonstram o raciocínio visual; não são prova de timing final ou comparação matemática de pixels.

Leitura somente dos cabeçalhos dos cinco PSDs recebidos (sem salvar, converter ou alterar): todos são PSD versão 1, RGB, 8 bits, quatro canais no cabeçalho.

| Nome em Downloads | Dimensões verificadas |
|---|---|
| `Imagem do ChatGPT 15 de out. de 2026, 15_11_11-1.psd` | 744 × 1636 |
| `Imagem do ChatGPT 15 de out. de 2026, 15_11_11-1 2.psd` | 744 × 1636 |
| `Imagem do ChatGPT 15 de out. de 2026, 15_11_12-2.psd` | 499 × 915 |
| `Imagem do ChatGPT 15 de out. de 2026, 15_11_13-3.psd` | 255 × 247 |
| `Imagem do ChatGPT 15 de out. de 2026, 15_11_13-4.psd` | 646 × 1232 |

O par `15_11_11-1` / `15_11_11-1 2` tem o mesmo canvas, coerente com a técnica explicada. Essa leitura não verifica máscaras, nomes de camadas, equivalência de pixels nem qual opção de importação foi usada. Não identificar a função de uma camada somente pelo sufixo `2`; inspecionar o PSD quando houver pedido de uso.

Antes de apresentar montagem: conferir base sozinha sem buracos, camiseta sob a frente sem gola amputada, acessórios no lugar, calça não duplicada, registro do par e entradas corretas. Movimentar/escalar o look deve preservar a relação base/frente; não ajustar uma delas independentemente por acidente. O gabarito completo não pode vazar na exportação.

## Cintos e tênis — correção reforçada por Lucas em 17/10/2026

O erro observado no 177 foi isolar o objeto com recorte apertado em vez de fundir os dois estados. O procedimento obrigatório é: imagem **sem** cinto/tênis embaixo; imagem **com** cinto/tênis sobreposta; alinhamento das partes comuns antes da máscara; máscara na imagem superior até perto do objeto, conservando uma faixa generosa da roupa para a transição; **feather amplo e bem esfumado somente nessa junção**. A base inferior permanece intacta e visível. Não trocar a roupa inteira, não redesenhar a barra/cintura e não desfocar o objeto inteiro.

A máscara deve permanecer editável: preferir PSD com pixels originais e máscara de camada ou máscara de Opacidade no Premiere, quando verificada. PNG alpha é apenas derivado e exige PSD/original+máscara preservados. Exportar sem redução de resolução; dimensionar a instância no Premiere. Registrar imagens dos dois estados, hashes, transformação de alinhamento, região da máscara, feather aplicado e comparação antes/depois da entrada. O valor do feather depende da escala e do contato, nunca de uma constante universal.

Lucas indicou como exemplo a correção que ele próprio fez no **cinto feminino da cena 1 do 177**. Consultar em modo somente leitura; não modificar nem substituir o trabalho pronto. Não presumir que essa máscara foi incorporada ao PSD: ela pode estar no clipe do Premiere. A inspeção deve identificar onde está a máscara e registrar o que de fato foi observado.


## Correção visual de Lucas — 17/10/2026, após a primeira prévia do tênis

A imagem enviada por Lucas mostra os dois tênis nítidos e uma faixa generosa de calça acima deles; a borda superior recortada dessa faixa fica bastante esfumada. Lucas especificou: “bordas da calça esfumadas (quanto mais esfumado o feather melhor)”. Essa orientação substitui “faixa mínima/pequena” e a interpretação de feather discreto.

Na imagem superior calça + tênis, manter tecido suficiente acima das barras para uma transição ampla, seguindo o desenho diagonal da referência. Aplicar bastante feather à borda criada pela máscara na calça, sem borrar os pixels RGB, logotipos, solas ou contornos dos tênis. Não recortar rente ao limite da calça-base, não limitar a faixa a poucos pixels e não usar a silhueta da base como trava para estreitar novamente a máscara. A calça-base inferior fica intacta. Conferir o recorte isolado sobre xadrez e a recomposição antes/depois da entrada. Ajustar a largura do esfumado pela referência e pela resolução nativa; não impor 2 px nem outro valor universal.

Preservar originais e máscara recuperável. Reabertura por psd-tools e hashes de pixels verificam recuperação nessa biblioteca, não abertura no Photoshop. Registrar separadamente validação estrutural do PSD e abertura no aplicativo; não declarar a segunda sem observá-la.
