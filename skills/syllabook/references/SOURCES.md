# Sources: research, user materials, fact checks and copyright

## Contents

1. Trust order
2. Research
3. The user's materials
4. Citing in the book
5. Fact checks
6. Copyright
7. Real images
8. Sensitive topics

## 1. Trust order

1. Official documentation, standards, specifications, release notes; primary sources (original documents, data, papers).
2. The project's official repository; museums, archives and universities.
3. Recognized textbooks and courses; peer-reviewed reviews; blogs by maintainers or institutions with authority on the topic.
4. Forums and Q&A sites **only** to learn which mistakes are common, never as the source of a fact.

**Encyclopedias** (Wikipedia, Britannica) are a map, not a source: use them to find the primary sources, the dates in dispute and the names to look up, then open what they cite and cite that. This holds when writing chapters too: an encyclopedia never goes in a chapter's Sources (`audit.py` blocks wikipedia.org and britannica.com there). A fact only an encyclopedia gives stays out of the book; the text may name the encyclopedia as the map that led to a source, without a link in Sources.

Anything that can change over time (commands, options, defaults, limits, versions, prices, laws) must come from levels 1–2 and be **checked in this session**. Stable concepts (what a variable is, what a verb tense is) need no source.

## 2. Research

- **Search in English by default**, whatever the book language: it has the most documentation, courses and references. Add sources in the book language when they are the best for the topic (the country's laws, school curricula or exams, the grammar of the book language, official documentation translated by the project itself).
- Search with a specific question; read only the part of a page that answers it.
- Stop as soon as you have what the step asks for (`modes/CREATE.md` §3).
- Record every source in `book.yaml` (`sources`: title, URL, checked date).
- **A checked date means you opened the page in this session and it says what the book uses it for.** A link seen only in search results is not checked: open it before giving it a date (in a dossier, `book.yaml` or a chapter's Sources), or leave it out. If it cannot be opened, cite it without a date and say so in the final summary.

**Research dossiers** (step 3 of the flow in `SKILL.md`, before writing any chapter): open every source in `book.yaml` once in this session and update its checked date; then, for **every** chapter of the book, write `research/c<nn>.md` (e.g. `research/c03.md`), even when the user asked to write only some chapters now: the dossiers are the judgment of the whole book, made before any chapter:

- the facts the chapter will state that can change over time (commands, options, defaults, limits, versions, laws), one per line, each with its link and the date checked;
- the official examples worth adapting, the common mistakes and any open question;
- short notes **in the book language**, not prose to translate; commands, options, error messages and short quotations stay in their original form.

Write `research/guide.md` too: the topic guide, starting from the approved "How this book teaches" block of the assessment and detailed with what the research showed (the kind of practice with its sources, how the reader checks themself, the diagram types to use, safety, what to avoid). It adapts the area profile to this topic; `book.py brief` gives it to every chapter.

Look across the whole book while you do it: if chapter 8 needs something chapter 3 should prepare, note it in both dossiers. The dossiers stay in the library (they show where each fact came from and help update the book) but are not part of the EPUB, the website or Notion. Chapters are written from their dossier and search again only for a fact it does not have.

## 3. The user's materials

Books, PDFs, EPUBs, Notion pages or Drive files the user sends:

- Run `ingest.py` and work from the outline; read only the sections a step needs.
- Use them to **understand, structure and check**. Never copy their text, examples or exercises.
- Cite them like any source ("<Title>, ch. 3"). They are never published or attached to the book.
- In Google Drive, list what the search found and open only what the user chooses.

## 4. Citing in the book

- Each chapter ends with `## 📚 Sources`: 2–6 links with their checked date.
- Version-dependent behavior names the version in the text ("since version 25, ...").
- Quotations: at most one short quotation (under 15 words) per source, in quotation marks, with the link, and only when the exact words matter.

## 5. Fact checks

For each chapter, `facts.py <n>` lists the sentences with dates, numbers, names and quotations. For each one:

1. Find it in the chapter's dossier; if it is not there, open the source page (or search once) and add it to the dossier.
2. If it holds, keep it; if it does not, fix it. Remove it, or say clearly that it is uncertain, only after looking for it and not finding it.
3. When the text says what a command or piece of code does, its real output in the chapter must show it (for example, the name a container really gets). If the output disagrees, the text is wrong.

Separate **fact**, **interpretation** and **legend** in the text whenever a topic has popular stories or debate ("The popular version says...; the records show..."). This is mandatory in the `knowledge` profile.

## 6. Copyright

- Explain in your own words. Paraphrasing means rewriting the explanation, not swapping synonyms.
- Write your own examples, exercises and code. A short snippet from documentation, when unavoidable, carries its source; respect the license of any reused code.
- Never reproduce song lyrics, poems or long passages of protected works. In music books, use public-domain songs or exercises written for the book.
- Third-party material in mode 2: only its structure, topics and goals; the original is never published.
- No third-party logos, brands or mascots, in images or on the cover.

## 7. Real images

Photos of people, events, machines, instruments, components or historical documents, and screenshots of the application the book builds:

- **Photos:** `images.py search "<query>"` lists only public domain, CC0, CC BY and CC BY-SA images from Wikimedia Commons and Openverse (search in English); `images.py fetch <fetch> --name c03-eniac` (the `fetch` value of a result: `File:<title>` or `openverse:<id>`) downloads one and records author, license and link in `img/CREDITS.md`. Never take a photo from a stock site or any other page.
- **Screenshots:** of a web page, after the step the reader just did, `images.py screenshot <url> --name c05-app`. Of VS Code, `images.py editor <folder> --name c03-vscode` (`VISUALS.md` §5). Of another desktop application (an installer, a settings screen, Docker Desktop, the Task Manager), first look in the vendor's own documentation repository on GitHub: `images.py docs <owner/repo> "<words>"` (for example `docker/docs`, `MicrosoftDocs/WSL`, `MicrosoftDocs/windows-dev-docs`, `microsoft/vscode-docs`; words in English, as in file names) lists its images only when the repository's license allows reuse with credit; look at each one, then `images.py fetch github:<owner/repo>/<path> --name c02-virtualizacao`. If the image shows an older version than the book's, say so in the caption. `fetch` brings a large image to 1600 pixels wide by itself when Pillow is installed; when its answer says the size instead, ask to install Pillow, or keep the image if it is under 1 MB. When no repository has it, write the step in text (what to click, what the reader sees) and go on: never stop the book waiting for a screenshot. Ask the user only if they offered to take screenshots; then record it in `img/CREDITS.md` yourself. Never draw or fake a screenshot.
- Put the credit in the caption (`images.py` prints it) and write the alt text.
- Which to use, an SVG or a real image, depends on what the reader must see (`VISUALS.md` §1): how parts relate is an SVG; how a real thing looks is a real image.
- `audit.py` reports a photo or screenshot without its line in `img/CREDITS.md` as an error.

## 8. Sensitive topics

- Health, law, finance, safety: official sources only, and a short note that the book does not replace a professional.
- Electronics, tools, chemistry or anything with physical risk: a safety box before the first hands-on step (see the `skills` profile).
- Topics that change fast (technology, laws): set `review_by` in `book.yaml`, usually 12 months after the check.
