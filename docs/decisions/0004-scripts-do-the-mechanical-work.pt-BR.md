<!-- translation-of: 0004-scripts-do-the-mechanical-work.md sha256:21afd2731b58 -->
# 4. Scripts fazem o trabalho mecânico

[English](0004-scripts-do-the-mechanical-work.md) | **Português**

**Situação:** aceita · **Origem:** `plano/PLANO.md §20`

## Contexto

Esqueletos, navegação, links do glossário, o EPUB, o site e as checagens são repetitivos; escritos pelo modelo, gastam tokens e variam de livro para livro.

## Decisão

O Claude escreve as explicações; scripts em Python fazem todo o resto e imprimem um JSON curto só com o que exige ação. Diagramas são especificações curtas que um script desenha.

## Consequências

Os livros saem consistentes e mais baratos, e os scripts têm testes no CI. A skill manda o Claude rodar os scripts, nunca lê-los.
