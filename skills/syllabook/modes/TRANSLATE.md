# Mode 3: Translate a book into another language

Follow this checklist. Track it yourself and never show it to the user: they see the results of each step, not the list.

```text
- [ ] 1. Identify the book and the target language
- [ ] 2. Glossary and adaptation notes (approved by the user)
- [ ] 3. Create the sibling book
- [ ] 4. Chapter loop (translate and adapt)
- [ ] 5. Fixed parts and images in the new language
- [ ] 6. Link both versions and publish
```

Translating here means **adapting**: the reader of the new version must feel the book was written for them.

## 1. Identify the book

The original comes from one of three places, in this order of preference:

1. **A book of the user's library** (the usual case, and the best: it keeps the code, the diagram specs, the concept graph and the sources). The library is the folder the session works in, or the user's repository, never the skill's own folder, even when its name sounds like a library: look in `created-books/` and `improved-materials/`. A library that is only on GitHub is cloned (or the book's folder downloaded) before starting. Read only `book.yaml` and the glossary.
2. **A zip this skill delivered** (it carries `book.yaml`): unzip it into the library as the original (`created-books/<slug>/`), then go on as in 1.
3. **A file the user sends**: PDF, EPUB, DOCX, ODT, RTF, HTML, a web page or Markdown; PPTX and images through Docling (`ingest.py` lists what it reads; a PDF keeps its tables and headings only with Docling, see the note `ingest.py` prints). Before anything, ask whether they wrote it or its license allows translations (public domain, CC BY, CC BY-SA). All rights reserved, or a license with no derivatives (ND): do not translate it; offer mode 2 (Improve), which writes a new book in their own words from it. With the right confirmed, run `python scripts/ingest.py <file> --out translated-books/<slug>-<lang>/original`, read the outline, and map each chapter of the original to its sections. An EPUB or PDF made by this skill is better taken from the library or the zip when the user still has them: the file has lost the specs and the graph.

Then confirm the target language and the conversation language.

**Language-learning books are adapted, not translated.** A book teaching English to Portuguese speakers cannot simply become a book for Spanish speakers: false friends, pronunciation traps and grammar contrasts change. Say so in one sentence and treat the examples about the learner's native language as content to rewrite.

**When the target language is the language the book teaches** (a book teaching English, written in Portuguese, into English), stop before the glossary: the new version no longer serves the original reader, who is learning that language from zero, and fits no reader by default. Ask the user who it is for, with the choices in one message (for example: learners of the same language with another native language, written in that native language; teachers of that language). Each answer is a different book: the contrasts, false friends and examples are rewritten for the chosen reader. A reader whose native language is the target language is not a translation: offer mode 1 (Create).

## 2. Glossary and adaptation notes

Before chapter 1, build a term table from the concept graph and the book's glossary: `original term → term in the target language`, using the terms people in that language actually use (for technology, often the English term). List also what will be adapted: names in examples, currencies, units, dates, cultural references, sources available in the target language.

Show both in one message and wait for "approved". The table goes into the new `book.yaml` (`glossary`) and every chapter follows it.

## 3. Create the sibling book

- Folder: `translated-books/<slug>-<lang>/`, whatever the original's collection (the original stays in `created-books/` or `improved-materials/`).
- From a file (§1, item 3): write `book.yaml` from the outline, one chapter per chapter of the original (same order, titles translated), each with `sources_original` (its sections in `original/`), the concepts from its headings and the sources it cites; set `translation_of` to the original's slug and `original: {title, author, where: original, rights: own | <license>}`. `book.py validate` refuses it without them.
- From the library: `book.yaml`: copy the original's, then set `language`, `translation_of: <slug>`, the translated titles and concept names, `edition: "1.0"`, `approved_on` (today, once the glossary is approved), and empty `progress`, `changes`, `editions` and `handoff` lists (the history belongs to the original). Add `translations: [<slug>-<lang>]` to the original.
- Run `book.py validate`.

## 4. Chapter loop

Use the loop in `SKILL.md`, with these differences:

- `book.py brief <n>` also gives the original chapter (`original_chapter`: its path in the library, or the list of its sections in `original/` for a file): read it, translate and adapt it into the new file. Do not add or remove content.
- **Code:** stays identical; translate only comments and user-facing strings when they are part of the lesson. `projects.py` runs everything again.
- **Commands and outputs:** keep the real outputs; translate only the explanation around them.
- **Sources:** keep the originals; add a source in the target language when one exists and says the same.
- **Facts:** `facts.py` is still run, because adapted examples can introduce new numbers or names.

## 5. Fixed parts and images

- Chapter 0, placement test, mock exam, glossary and map: regenerate with `build.py` in the new language; translate their texts like a chapter. The book on one page and the cheat sheets are `cards` specs: translate them like any diagram (next line), keeping the label of the new language.
- **SVG diagrams:** translate the text in each spec and redraw with `diagram.py`; never edit a diagram's SVG by hand.
- **SVG illustrations** (no spec in `img/_source/`): translate only the `<title>` and the labels in the SVG, then run `illustration.py`.
- **Real images:** keep them; translate captions and alt text; keep the credits.

## 6. Link and publish

- Each version's README links to the other ("Also available in: ...").
- Run `audit.py` on the whole book, then `build.py`, then publish as in `modes/PUBLISH.md` §3–4.
