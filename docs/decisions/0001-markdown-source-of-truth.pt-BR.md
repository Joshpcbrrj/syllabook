<!-- translation-of: 0001-markdown-source-of-truth.md sha256:931c14c8e79b -->
# 1. O Markdown é a fonte da verdade

[English](0001-markdown-source-of-truth.md) | **Português**

**Situação:** aceita · **Origem:** `plano/PLANO.md §2, §8`

## Contexto

Os livros ficavam no Notion, que é difícil de versionar, testar ou publicar em outro lugar.

## Decisão

Cada livro é uma pasta de arquivos Markdown com um `book.yaml`, num repositório Git. O EPUB, o site e a cópia no Notion saem dele no fim.

## Consequências

Os livros podem ser testados, comparados e publicados de graça (GitHub Pages e releases). O Notion é uma cópia: o que for editado lá não volta para o livro.
