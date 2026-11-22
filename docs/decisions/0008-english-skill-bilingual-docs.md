# 8. The skill is in English; the documentation in English and Portuguese

**English** | [Português](0008-english-skill-bilingual-docs.pt-BR.md)

**Status:** accepted · **Source:** `plano/PLANO.md §22`

## Context

The project was born in Portuguese, but English reaches more people, and the model follows English instructions well in any conversation language.

## Decision

The skill, identifiers and messages are written in English; Claude talks and writes each book in the language the user chooses. The documentation is in English with a Portuguese version next to it; each translation records the hash of the English page it translated.

## Consequences

A test warns when an English page changes and its translation does not. Each book language has a short style file so the text does not sound translated.
