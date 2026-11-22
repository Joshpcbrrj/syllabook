# 5. What the reader reproduces stays as text

**English** | [Português](0005-reproducible-content-as-text.pt-BR.md)

**Status:** accepted · **Source:** `plano/PLANO.md §2, §10`

## Context

Code, commands or chords inside an image cannot be copied, searched, read by a screen reader or translated.

## Decision

Code, formulas, commands, chords and step-by-step instructions are always text (code blocks). Images only show what is easier to see than to read.

## Consequences

It is one of the skill's "Never" rules, and the audit refuses any image without alt text. Hidden answers use `<details>` in Markdown and on the website, and an appendix with links both ways in the EPUB.
