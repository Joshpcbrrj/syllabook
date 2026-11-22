<!-- translation-of: 0003-segmented-chat-no-agents.md sha256:fbe0791aa51b -->
# 3. Um capítulo por vez, sem agentes

[English](0003-segmented-chat-no-agents.md) | **Português**

**Situação:** aceita · **Origem:** `plano/PLANO.md §2, §20`

## Contexto

Escrever um livro gasta muitos tokens, e o dono quer que caiba numa assinatura comum. A Anthropic mediu que um agente gasta umas 4 vezes, e um sistema com vários agentes umas 15 vezes, os tokens de um chat; e os capítulos de um livro dependem uns dos outros, o caso em que vários agentes funcionam mal.

## Decisão

O livro é escrito um capítulo por vez, em ordem, com um briefing compacto e o texto gravado em arquivo. Sem agentes nem capítulos em paralelo. Depois de uns três capítulos, a skill sugere uma conversa nova e deixa uma nota de passagem no `book.yaml`.

## Consequências

Cada capítulo começa do briefing e do resumo do anterior, não da conversa inteira. Um livro longo atravessa várias conversas sem perder nada entre elas.
