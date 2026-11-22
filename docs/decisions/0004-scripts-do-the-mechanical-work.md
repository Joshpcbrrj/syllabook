# 4. Scripts do the mechanical work

**English** | [Português](0004-scripts-do-the-mechanical-work.pt-BR.md)

**Status:** accepted · **Source:** `plano/PLANO.md §20`

## Context

Skeletons, navigation, glossary links, the EPUB, the website and the checks are repetitive; written by the model, they cost tokens and vary from book to book.

## Decision

Claude writes the explanations; Python scripts do everything else and print short JSON with only what needs action. Diagrams are short specs that a script draws.

## Consequences

Books come out consistent and cheaper, and the scripts are covered by tests in CI. The skill tells Claude to run the scripts, never to read them.
