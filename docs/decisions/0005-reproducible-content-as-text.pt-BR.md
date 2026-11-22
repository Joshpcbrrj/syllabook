<!-- translation-of: 0005-reproducible-content-as-text.md sha256:393020b95fb5 -->
# 5. O que o leitor reproduz fica em texto

[English](0005-reproducible-content-as-text.md) | **Português**

**Situação:** aceita · **Origem:** `plano/PLANO.md §2, §10`

## Contexto

Código, comandos ou cifras dentro de uma imagem não podem ser copiados, buscados, lidos por um leitor de tela nem traduzidos.

## Decisão

Código, fórmulas, comandos, cifras e passo a passo ficam sempre em texto (blocos de código). As imagens só mostram o que é mais fácil de ver do que de ler.

## Consequências

É uma das regras "Never" da skill, e a auditoria recusa qualquer imagem sem texto alternativo. As respostas escondidas usam `<details>` no Markdown e no site, e um apêndice com links de ida e volta no EPUB.
