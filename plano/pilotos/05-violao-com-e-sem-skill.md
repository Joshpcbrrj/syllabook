# Piloto 5: violão com e sem a skill (2026-11-26)

**Pergunta:** a skill ensina melhor do que o Claude sozinho, recebendo o mesmo pedido? **Escopo combinado:** parecer, ementa e capítulos 1 a 3.

## Como foi feito

- **Mesmo pedido** nos dois lados (o do piloto 3), com as respostas das perguntas iniciais já incluídas: nunca tocou, violão de nylon, gosta de MPB e pop, tamanho "livro". O lado com a skill diz "com o Syllabook"; o outro, não.
- **Mesmo modelo por etapa:** Opus para a ementa, Sonnet para os capítulos (a dica da própria skill). Mesmas ferramentas (shell, arquivos, busca e leitura na web), sem conectores (`--strict-mcp-config`).
- **Sem a skill:** todas as skills desligadas (`--disable-slash-commands`), numa pasta vazia. **Com a skill:** o plugin do repositório, numa biblioteca feita do modelo.
- Cada etapa numa sessão nova, com mensagem autocontida. Scripts e respostas em `C:\Users\joshp\syllabook-pilotos\` (`violao_turn.py`, `violao-*-turn-*.md`, `violao-costs.jsonl`).

## Resultado em números

| | Com a skill | Sem a skill |
| --- | --- | --- |
| Pediu aprovação da ementa antes de escrever | sim | **não**: escreveu o livro inteiro na primeira resposta |
| Custo até os caps. 1 a 3 | US$ 2,69 (ementa 0,63 + pesquisa dos 11 caps. e caps. 0 a 3: 2,06) | US$ 1,48 (o livro inteiro, de uma vez) |
| Tempo | 1,7 + 10,7 min | 6,3 min |
| Formato | Markdown por capítulo, `book.yaml`, pesquisa por capítulo, EPUB e site pelo `build.py` | um HTML só, que depende de JavaScript |
| Palavras por capítulo (caps. 1 a 3) | 2.144 a 2.684 | 635 a 786 |
| Exercícios com resposta comentada | 4 por capítulo, mais 4 de revisão, todos com resposta escondida | metas para marcar, **sem resposta** |
| Fontes | com link e data em cada capítulo; dois artigos científicos no parecer | **nenhuma** |
| Diagramas | 8 SVG (acordes, cordas, batida, compasso, prática intercalada) mais 1 foto com licença livre e crédito; tudo também em texto copiável | acordes desenhados por JavaScript, só no navegador; sem texto alternativo |

## Correção

**Os dois lados acertaram o que conferi.** Nos dois: digitação dos acordes, nota por corda e posição dos dedos. Com a skill: Em, Am, G, C, D e A, as frequências da afinação, o método de afinar de ouvido (com a exceção da casa 4), a batida pop e as contas de bpm. Sem a skill: as 12 digitações, a régua de notas das cordas 6 e 5 e o truque das oitavas. Nenhum erro de conteúdo encontrado nos caps. 1 a 3.

## Didática (onde está a diferença)

1. **Vitória no primeiro dia.** Com a skill, o cap. 1 termina com a pessoa tocando Em e Am no tempo. Sem a skill, o cap. 2 é teoria (12 notas, semicolcheias, síncope) e o primeiro acorde só vem no cap. 3, por volta da semana 3: é onde muito iniciante desiste.
2. **Ensina o porquê.** Com a skill: por que a corda 6 fica de fora no Am, por que afinar duas vezes, o "segredo da troca" (o bloco de dedos desce uma corda) e o A com dedos 2-1-3, para o dedo 1 não sair do lugar na troca D→A. Sem a skill, as regras aparecem sem o porquê.
3. **Prática que se confere sozinho.** Com a skill, cada capítulo tem uma rotina com minutos, um critério de "pronto" medido ("8 trocas sem parar", "1 minuto a 70 bpm"), exemplo resolvido, exercício de completar, exercício livre, desafio com gravação de si mesmo e lista para conferir a gravação. Sem a skill há metas boas, mas sem retorno: quem estuda sozinho não sabe se acertou.
4. **Honestidade sobre a evidência.** Com a skill, o parecer separa o que a pesquisa sustenta (prática intercalada) do que ainda é inconclusivo em música (espaçamento), e o cap. 2 mostra duas fontes que discordam sobre como subir o andamento. Sem a skill, a lista de "o que a pesquisa mostra" vem sem nenhuma fonte.
5. **Segurança.** Só a skill traz o quadro de dor normal × dor que manda parar, logo no início, e repete o aviso na batida.
6. **Onde o lado sem a skill foi bem:** sugestões de repertório real (títulos de músicas, sem letras), a pressão mínima explicada como teste, o exercício "aranha" de mão esquerda e o desafio de "trocas em 1 minuto". São boas ideias, que a skill pode aproveitar (abaixo).

## O que a skill deve melhorar

1. **Postura em figura de verdade.** O diagrama de postura são duas colunas de texto ("Evite" × "Procure"). Para o corpo, um desenho simples (ilustração SVG, `VISUALS.md` §4b) ou uma foto livre mostra mais. Regra a acrescentar no perfil `skills`: postura e posição das mãos pedem figura do corpo, não lista.
2. **Repertório.** O livro com a skill não sugere músicas reais para aplicar o que se aprendeu; só ensina a ler a cifra que a pessoa achar. Sugerir títulos (sem letra nem cifra) é permitido e motiva: acrescentar ao perfil `skills`.
3. **Fonte pela busca.** Uma fonte do cap. 1 está marcada "pelo resultado da busca", sem a página ter sido aberta. A regra do `SOURCES.md` é abrir cada fonte. A skill foi honesta ao marcar, mas o certo é abrir ou tirar.
4. **Crédito da foto.** O texto saiu como "The original uploader was Piero Sagnibene at Italian Wikipedia .", copiado do campo do Commons. O `images.py` pode limpar esse padrão para "Piero Sagnibene (Wikipedia em italiano)".
5. **Áudio.** Nenhum dos dois lados resolve o maior limite de um livro de violão: não se ouve o ritmo. A skill avisa e ensina a se gravar, o que é o certo sem áudio. Uma saída futura seria indicar faixas de referência ou um metrônomo com padrão, sem inventar links.

## Conclusão

**A skill cumpre o propósito de aprendizado, e a diferença não é de correção: é de ensino.** Os dois lados acertam os fatos. Mas só a skill entrega um material que ensina sozinho: começa pelo que a pessoa consegue fazer no primeiro dia, explica o porquê, dá prática que se confere sem professor, mostra de onde vem cada afirmação e funciona fora do navegador (EPUB, site, Notion). O Claude sem a skill entrega em 6 minutos um bom roteiro de anotações, com 600 a 800 palavras por capítulo e sem retorno nem fontes. Para quem já toca, serve como guia. Para quem nunca tocou e estuda sozinho, faltam as partes que mantêm a pessoa estudando. O custo da skill até aqui (US$ 2,69 para ementa, pesquisa do livro inteiro e 4 capítulos) indica um livro completo na faixa de US$ 8 a 12.
