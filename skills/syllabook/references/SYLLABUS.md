# Syllabus: the `book.yaml` file

`book.yaml` is the book's contract and its memory: the approved syllabus, the user's choices and the progress. Scripts read it; you keep it up to date only through the steps that say so. Run `python scripts/book.py validate <book.yaml>` after every change.

## Model

```yaml
title: "Docker Compose na prática"
subtitle: "Do primeiro compose.yaml a uma stack completa"
slug: docker-compose-na-pratica      # lowercase ASCII and hyphens; folder name
origin: created                      # created | improved
language: pt-BR                      # book language
conversation_language: pt-BR
profiles: [stem]                     # stem | languages | skills | knowledge (at most 2)
level: {start: iniciante, end: intermediário}   # in the book language: the library lists show it as written
audience: "Who already runs containers with docker run"
goal: "Describe an app with API, database and proxy in one compose.yaml and run it with one command"
prerequisites: ["docker-do-zero"]    # slugs of other books, or plain text
track: {name: devops, order: 2}      # a series of books, in reading order; the front page lists the library by track
                                     # a NEW track also gets its display name in library.yaml, in the library's
                                     # language (tracks: {devops: "DevOps"}); without it, "devops" shows as "Devops"
continues: {book: docker-do-zero, step: 1}   # only for a next book (CREATE.md §7): the earlier book and its next step
reference_version: "Docker Compose v5.6, Docker Engine 29.9"   # only if the topic changes over time
review_by: "2027-11"                 # month to review it by (modes/REVIEW.md); the library lists warn after it
reviewed_on: ""                      # filled by book.py edition at the end of a review
editions: []                         # filled by book.py edition: {edition, date, summary}
notion_url: ""                       # the book's page in Notion, saved after the copy (PUBLISH.md §4)
sources:
  - {title: "How Compose works", url: "https://docs.docker.com/compose/intro/compose-application-model/", checked: "2026-11-17"}
approved_on: ""                      # empty while it is a draft
edition: "1.0"
human_review: false
choices: {images: real, reading: large}  # images: real (SVG + real images by context) | svg; reading: large | small
concepts:                            # the concept graph
  - {id: service, name: "serviço", chapter: 1, depends: []}
  - {id: project-network, name: "rede do projeto", chapter: 6, depends: [service]}
chapters:
  - n: 1
    title: "Por que um arquivo para o projeto"
    goal: "Rebuild a long docker run as a compose.yaml"
    topics: ["declarative vs imperative", "services"]
    minutes: 35
    sources_original: []             # mode 2: sections of the original this chapter comes from
next_steps:                          # 2–4 later books; build.py writes them at the end of the last chapter
  - {title: "Compose avançado", why: "Para levar o projeto a produção com segurança", topics: ["profiles", "secrets", "healthchecks"]}
  - {title: "Kubernetes do zero", why: "Para rodar em vários servidores", topics: ["pods", "deployments", "services"]}
covers: [compose, compose-yaml]      # short stable labels, used to compare books in a track
progress: []                         # filled by book.py done: {n, done, reread, summary}
changes: []                          # changes after approval: {date, what, why}
handoff: []                          # book.py handoff: what is pending for the next conversation
```

Mode-specific fields:

- **Improve (mode 2):** `origin: improved`; `original: {title, kind, where}` (where it came from, never published); `promise: {goal, audience, level, sequence}`; `sources_original` in each chapter; `new_content_pct`.
- **Translate (mode 3):** `translation_of: <slug>`; `glossary: [{source, target}]`; the original gets `translations: [<slug>-<lang>]`.

## Goals

The book's `goal` and each chapter's `goal` say what the reader **will be able to do**, so they and the review can check it: one or more verbs whose result can be shown or tested ("build", "calculate", "explain in two sentences", "translate", "play at 80 bpm", "order on a timeline"). `book.py validate` warns about a weak verb anywhere in the goal; fix every such warning before showing the syllabus, and check the goals yourself when code execution is not available.

| Weak (never, not even as one verb of a list) | Rewrite as |
| --- | --- |
| understand, know, learn about, be familiar with | explain, tell apart, predict, choose, use |
| entender, compreender, conhecer, saber, aprender sobre | explicar, distinguir, prever, escolher, usar |
| comprender, conocer | explicar, distinguir, elegir, usar |

Every goal **starts with a verb** (infinitive in Portuguese and Spanish: "Clonar", "Explicar"). A list of commands or topics is not a goal: it says what the chapter covers, not what the reader will do.

- "`clone`, `push`, `pull` e `fetch`, com autenticação segura" → "Clonar um repositório, enviar e receber mudanças com `push` e `pull`, e autenticar por SSH".
- "Entender, resolver e evitar conflitos" → "Resolver um conflito de merge e evitar os mais comuns".
- "Declarar volume nomeado e entender a diferença entre down e down -v" → "Declarar um volume nomeado e prever o que `down` e `down -v` apagam".
- "Know the main battles of the war" → "Place the main battles on a map and a timeline".

## Concept graph rules

- Every concept that a chapter teaches is listed once, with the chapter that teaches it.
- `depends` lists the concepts it needs. `book.py validate` refuses a concept that depends on one taught in a later chapter.
- A concept taught by an earlier book (one in `prerequisites`) is written `<slug>:<concept id>` in `depends` (`docker-do-zero:container`); `book.py validate` checks it when that book is in the library.
- Keep it short: the 3–8 key concepts of each chapter, not every term. `build.py` uses it for the map, the glossary links and the index.

## Labels

`covers` and the ids in `concepts` are short, stable, lowercase, ASCII and hyphenated (`compose-yaml`), whatever the book language. `name` and the titles are in the book language.

## Changes after approval

1. Show the impact first ("dropping ch. 5 affects the examples in ch. 6 and 8").
2. Ask approval for that change only.
3. Update the chapters and concepts, add an entry to `changes` (date, what, why), and run `book.py validate`.
4. If chapters already written are affected, list them and fix them before continuing.

Do not change `approved_on`: the original approval date stays; `changes` holds the history (and git holds the rest).
