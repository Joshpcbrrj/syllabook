<!-- translation-of: tutorial.md sha256:757e04cabf1d -->
# Tutorial: seu primeiro livro

[English](tutorial.md) | **Português**

Neste tutorial você cria um livro a partir de um tema, da primeira mensagem até o site publicado. O exemplo é um livro de verdade: [Docker Compose na prática](https://joshpcbrrj.github.io/biblioteca-syllabook/), com 14 capítulos, escrito com o Syllabook em novembro de 2026. As mensagens abaixo mostram o formato do que o Syllabook diz, não uma transcrição, e o texto do seu livro vai ser outro.

## Conteúdo

- [Antes de começar](#antes-de-começar)
- [1. Peça o livro](#1-peça-o-livro)
- [2. Responda até três perguntas](#2-responda-até-três-perguntas)
- [3. Leia o parecer e a ementa](#3-leia-o-parecer-e-a-ementa)
- [4. Ajuste até ficar bom](#4-ajuste-até-ficar-bom)
- [5. Aprove e escolha imagens e leitura](#5-aprove-e-escolha-imagens-e-leitura)
- [6. Acompanhe os capítulos](#6-acompanhe-os-capítulos)
- [7. Continue numa conversa nova](#7-continue-numa-conversa-nova)
- [8. Publique](#8-publique)
- [O que você tem no fim](#o-que-você-tem-no-fim)

## Antes de começar

- **Syllabook instalado** no app do Claude ou no Claude Code: veja [Instalar](../README.pt-BR.md#instalar).
- **Opcional:** GitHub e Notion conectados ([integrações](integrations/README.pt-BR.md)). Sem eles você recebe o livro inteiro num zip, e o Syllabook pergunta de novo no fim.
- Para um livro de tecnologia, o Claude Code rende mais: ele roda os comandos no seu computador. No Windows, use-o dentro do [WSL 2](integrations/wsl.pt-BR.md).

## 1. Peça o livro

Diga o que quer aprender, com as suas palavras e no seu idioma:

```text
Quero aprender Docker Compose. Já uso docker run, mas quero subir um projeto com uma API e um banco de dados.
```

O Syllabook confirma o idioma em uma linha ("Vou conversar e escrever o livro em português (pt-BR). Quer mudar algum dos dois?"). Se o pedido não estiver claro, ele mostra o menu de sete opções; a opção 1 é "Criar um livro a partir de um tema".

## 2. Responda até três perguntas

Ele pergunta só o que o seu pedido não disse, no máximo três perguntas: o seu nível hoje, por que você quer aprender e o tamanho (guia curto, livro ou completo). Cada uma tem um padrão, então uma resposta curta basta:

```text
Uso docker run no trabalho. Um livro, não muito longo.
```

Ele também oferece usar os seus livros, PDFs ou uma pasta do Google Drive como fonte. Pode pular.

## 3. Leia o parecer e a ementa

O Syllabook pesquisa o tema (documentação oficial, duas ou três ementas de referência, os erros mais comuns) e responde numa mensagem só. Ela começa com o parecer: o que é o tema, o que ajuda saber antes, os erros comuns, a segurança, as fontes principais e como o livro vai ensinar. Depois vem a ementa:

```text
📘 Docker Compose na prática · iniciante → intermediário · 14 capítulos · ~10 h
Para quem: quem já roda contêineres com docker run e quer subir um projeto com vários serviços

0. Como estudar este livro
1. Por que um arquivo para o projeto → reconstruir um docker run longo como um compose.yaml
2. Instalar e conferir o Compose     → verificar o plugin no Docker Desktop e no Linux
3. Primeiro compose.yaml             → subir, listar, ver logs e derrubar com up, ps, logs e down
...
14. Projeto final: stack completa    → API, banco e proxy, em dev e produção, com um comando
    Simulado final

Ajuste à vontade: "mais longo", "mais curto", "tire o 5", "acrescente X", "junte 3 e 4"...
Quando estiver bom, diga "aprovado".
```

Nada foi escrito ainda. Cada capítulo tem um objetivo que dá para conferir, e nenhum capítulo usa um conceito que só um capítulo posterior ensina.

## 4. Ajuste até ficar bom

Peça mudanças com as suas palavras:

```text
Junte o 11 e o 12 e acrescente um capítulo sobre limites de CPU e memória.
```

Cada resposta começa com uma linha dizendo o que mudou, seguida da ementa inteira atualizada. Repita até gostar. Mudar a ementa custa uma mensagem; uma ementa errada custaria o livro inteiro.

## 5. Aprove e escolha imagens e leitura

```text
aprovado
```

O Syllabook grava a ementa no `book.yaml` e faz duas perguntas curtas, com padrão:

- **Imagens:** diagramas SVG mais imagens reais onde elas mostram melhor (fotos com licença livre, capturas de tela), ou só diagramas SVG.
- **Leitura:** telas grandes, ou um leitor de e-book pequeno em preto e branco (diagramas e linhas de código mais estreitos).

## 6. Acompanhe os capítulos

Primeiro o Syllabook escreve as notas de pesquisa de todos os capítulos; depois, os capítulos, um de cada vez. Em cada um ele escreve o texto, roda cada comando e cada trecho de código, confere os fatos com as fontes, relê como um leitor nativo e roda a auditoria. Você vê uma linha por capítulo:

```text
✅ Cap. 3/14: Primeiro compose.yaml
```

Quando um comando precisa do seu computador (o Docker, por exemplo) e a sessão não consegue rodá-lo, o Syllabook passa os comandos, você roda e cola só as linhas que ele pedir. Se preferir não rodar, o comando sai marcado como "não executado" no livro.

## 7. Continue numa conversa nova

Cada mensagem relê a conversa inteira, então depois de uns três capítulos o Syllabook sugere uma conversa nova, para poupar o seu limite de uso. Nada se perde: o progresso está no `book.yaml`. Abra uma conversa nova e diga:

```text
continue o meu livro Docker Compose na prática
```

Se um limite de uso acabar no meio de um capítulo, espere ele renovar e continue no mesmo chat.

## 8. Publique

Depois do último capítulo, o Syllabook escreve as partes fixas (capítulo 0, teste de nivelamento, cheat sheets, simulado, glossário), audita o livro inteiro, faz a capa, o EPUB e um zip, e publica:

- **Com GitHub:** no repositório da sua biblioteca; o GitHub Actions gera o site e o EPUB.
- **Com Notion:** uma cópia de cada capítulo embaixo da página que você escolher.
- **Sem conexões:** o zip, com as mesmas pastas de uma biblioteca, e o passo a passo para enviá-lo.

O resumo final traz os links, o que não foi executado e por quê, e os próximos livros sugeridos.

## O que você tem no fim

```text
created-books/docker-compose-na-pratica/
├── book.yaml      a ementa, as suas escolhas e o progresso
├── README.md      o mapa do livro, com links para cada capítulo
├── chapters/      00-como-estudar-este-livro.md ... 14-projeto-final-stack-completa.md, simulado, glossário
├── img/           diagramas e imagens, com o img/CREDITS.md
├── research/      as notas de pesquisa, com as fontes e as datas conferidas
└── projects/      o código dos projetos, montado a partir dos capítulos
```

Além do [site com busca](https://joshpcbrrj.github.io/biblioteca-syllabook/) e do EPUB na release `epubs` da biblioteca.

**Depois:** aprofunde com o próximo livro da trilha ("crie o próximo livro a partir do meu livro de Docker Compose") ou revise o livro mais tarde ("revise o meu livro de Docker Compose"). Os campos do `book.yaml` estão na [referência](reference.pt-BR.md).
