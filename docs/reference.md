# Reference: `book.yaml` and `library.yaml`

**English** | [Português](reference.pt-BR.md)

Two YAML files hold everything Syllabook knows about your books. You rarely need to edit them: the skill writes them as you talk. This page is for when you want to read one, fix a detail by hand, or understand what a script did.

After editing a `book.yaml` by hand, ask Syllabook to check the book, or run `python scripts/book.py validate <book.yaml>` yourself: it reports what is wrong, with the field name.

## Contents

- [Where the files are](#where-the-files-are)
- [`book.yaml`: the book](#bookyaml-the-book)
- [`library.yaml`: the library](#libraryyaml-the-library)

## Where the files are

```text
my-library/
├── library.yaml                    settings of the whole library
├── created-books/<slug>/book.yaml  a book created from a topic
├── improved-materials/<slug>/...   a material you improved
└── translated-books/<slug>-<lang>/ a translation (whatever the original's folder)
```

## `book.yaml`: the book

It is the book's contract and its memory: the approved syllabus, your choices and the progress.

### Required fields

`validate` refuses a book without any of these.

| Field | What it is |
| --- | --- |
| `title` | the book's title |
| `slug` | the folder name: lowercase letters, digits and hyphens (`docker-compose-na-pratica`) |
| `origin` | `created` (from a topic) or `improved` (from your material); a translation keeps its original's |
| `language` | the book language (`pt-BR`, `en`...) |
| `profiles` | 1 or 2 of `stem`, `languages`, `skills`, `knowledge`: how the book teaches |
| `level` | `{start, end}`, in the book language (`{start: iniciante, end: intermediário}`) |
| `audience` | who the book is for |
| `goal` | what the reader will be able to do at the end |
| `sources` | the sources: each one `{title, url, checked}`, with `checked` as `YYYY-MM-DD` |
| `approved_on` | the date you approved the syllabus; empty while it is a draft |
| `concepts` | the concept graph (below) |
| `chapters` | the chapters: `n` (1, 2, 3... with no gaps), `title`, `goal`, `topics` and `minutes` |

### The concept graph

Each concept the book teaches appears once: `{id, name, chapter, depends}`. `id` is a short label (`project-network`); `name` is in the book language. `depends` lists the concepts it needs, and `validate` refuses a concept that depends on one taught in a later chapter. A concept taught by an earlier book is written `<slug>:<id>` (`docker-do-zero:container`), and that book must be in `prerequisites`.

### Optional fields

| Field | What it is |
| --- | --- |
| `subtitle` | goes on the cover and the website |
| `conversation_language` | the language Syllabook talks to you in, if different from the book's |
| `choices` | `{images: real or svg, reading: large or small}`: real images where they help or diagrams only; large screens or a small e-reader |
| `prerequisites` | books the reader should know first: slugs of books in the library, or plain text |
| `track` | `{name, order}`: a series of books, in reading order; the library's front page lists books by track |
| `continues` | `{book, step}`: for a next book, the earlier book and which of its next steps this one follows (`book` must also be in `prerequisites`) |
| `next_steps` | 2 to 4 later books, each `{title, why, topics}`; they are written at the end of the last chapter |
| `covers` | short labels of what the book covers (`compose`, `compose-yaml`), used to compare books in a track |
| `reference_version` | the version the book is based on, for topics that change (`Docker Compose v5.6`) |
| `review_by` | the month to review the book by (`2027-11`); the library lists warn after it |
| `edition` | the current edition (`1.0`; `1.3` after a review; `1.3.1` for errata only) |
| `human_review` | `true` when a person reviewed the content |

Improved materials also have `original` (where the material came from; it is never published), `promise` (`{goal, audience, level, sequence}` of the original), `new_content_pct` and, in each chapter, `sources_original` (the sections of the original it comes from). Translations have `translation_of` (the original's slug) and `glossary`; the original gets `translations`.

### Filled in by Syllabook

Edit these only if you know why:

| Field | Written by |
| --- | --- |
| `progress` | `book.py done`: each finished chapter, with its date and summary |
| `changes` | the skill, for every change after approval: `{date, what, why}` |
| `handoff` | `book.py handoff`: what is pending for the next conversation |
| `editions`, `reviewed_on` | `book.py edition`, at the end of a review |

## `library.yaml`: the library

It sits at the root of your library repository. The skill fills it in the first time it sets up the library.

| Field | What it is |
| --- | --- |
| `author` | your name as it goes on the covers and in the EPUB |
| `repository` | `<owner>/<name>` of the library on GitHub; it gives the website and EPUB links |
| `branch` | the branch the books are published to (`main`) |
| `commit_name`, `commit_email` | the name and e-mail of the skill's commits; use the GitHub noreply address (`<user>@users.noreply.github.com`), never a personal e-mail |
| `default_language` | the conversation and book language for new books; `auto` = the language of your first message |
| `content_license`, `code_license` | the licenses of the text (`CC BY-SA 4.0`) and of the code (`MIT`) |
| `epub_release` | the GitHub release that holds the EPUBs (`epubs`) |
| `notion_page` | the Notion page where books are copied; the skill asks for it the first time |
| `site_title` | optional: the website's title (default: the repository name) |
| `tracks` | optional: display names of the tracks (`{devops: "DevOps"}`); without one, `devops` shows as "Devops" |
