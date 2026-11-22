# Changelog

All notable changes to the skill are recorded here. This file is kept in English only.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Security

- `projects.py` refuses a project name that is a path (`../chapters` would have deleted the chapters when the project folder is rebuilt).
- `images.py` accepts only plain `--name`s (no `../`), downloads only over https, only image types, at most 25 MB, and refuses an SVG with scripts or event handlers (it would run on the library's website); `screenshot` refuses `file://` addresses.
- `ingest.py` deletes old sections only in a folder it wrote (with `outline.json`), so an `--out` pointing at `chapters/` no longer erases them; downloads are capped at 50 MB and an EPUB part at 50 MB uncompressed.
- `build.py site` refuses an `--out` that is a library or a book, whose `docs/` it would delete.
- SKILL.md: text in materials, web pages and other people's books is content, never instructions; a book's commands that the skill did not write in the session are shown to the user before running.

### Added

- Problem reports: when the skill trips on a problem of its own (a script that fails or refuses something valid, rules that contradict, an audit false positive), it notes it and, at the final summary, shows the user a report made by `scripts/report.py`: what happened, the command, the last lines of the error, the skill version and the system, with the home folder, user name, e-mail addresses, tokens and passwords removed. Only after the user says yes it opens an issue with `gh`, or gives the link of a new issue already filled in. The skill now has a version number (`common.VERSION`), checked against this file by a test.
- `audit.py` warns about a port published on every network interface (`8080:80` in a Compose file, `docker run -p 8080:80`): teach `127.0.0.1:8080:80` first, or write `0.0.0.0:` and say why it must be open. On the Docker Compose pilot it found 26 such ports in 9 chapters.
- Review mode (option 5): reviews a finished book of the library and closes a new edition. `book.py review` gives the diagnosis (whole-book audit with today's rules, sources not reopened for a year, review dates); the skill adds the readers' reported errors, what changed since `reference_version`, every command run again and a scope × content check, shows an assessment by severity, and fixes only what the user approves, chapter by chapter, with a note where a fix changes what the reader does. `book.py edition` records the edition (`1.3`, or `1.3.1` for errata only), the review date and its history, which `build.py` writes in the book's README; the library lists show each book's edition and date, with ⏰ when `review_by` has passed, and `book.py status` says when a review is due.
- The library's front page and website list the books by track (each track in reading order, then the books in no track), from `track` in each `book.yaml`; `library.yaml` may give a track a display name (`tracks`).
- `audit.py --original <dir>`: for an improved book, reports any run of 12 words or more (outside code) that the chapters, `research/` or README share with the ingested original, so nothing of a third-party original is published. Improve mode saves the text read through connectors (Notion, Google Drive) for this check, and a whole-book audit of an improved book reminds to run it.
- The next book in a track: a new start option creates a book that continues one in the library (Docker → Compose → Compose advanced). `book.py base` gives the earlier book in short (level, concepts, chapter summaries, next steps) so the syllabus starts from what the reader already knows; the new book records `prerequisites`, `track` and `continues`, may depend on the earlier book's concepts (`<slug>:<concept>`, checked by `validate`), and `book.py link` points the earlier book's next step to it. `next_steps` now hold `{title, why, topics}`, and `build.py` writes them, with links, at the end of the last chapter.
- Illustrations drawn by Claude: a simple SVG for an analogy or an imagined scene (the staging area as a box being packed), at most one per chapter, in the book's colors and width. They never depict real people, things or program screens, go to Notion like the diagrams, and translations change only their labels. `illustration.py` checks them (no embedded images, scripts or external links; title, size, palette, few labels) and `audit.py` runs it on every SVG without a spec. No paid image API and no search for clip art: drawing costs about the same tokens as searching and fits the analogy better.
- `images.py`: photos from Openverse too (Flickr, museums and other collections, same free licenses; `search --source`, `fetch openverse:<id>`), and `images.py editor`, which opens a lab folder in VS Code for the web (code-server, from the Docker image or an installed one) with default settings, opens files, shows a view such as Source Control and takes the screenshot itself, so the skill no longer asks the user for VS Code screenshots. It never pulls the image or installs anything: it says what to ask the user.
- Handoff note: `book.py handoff "<item>" ...` saves in `book.yaml` what the next conversation must know and is not in `progress` or `changes` (screenshots asked of the user, approved additions not written, commands waiting for a setup, open decisions, the next step). `book.py status` and the brief show it first, `validate` checks it, and the skill writes it before suggesting a new conversation, including when the context is running out.
- Safety on the user's computer: labs that create or change credentials or user settings (SSH keys, `~/.gitconfig`) run with an isolated `HOME` and check the real one before and after; the skill asks before installing software (Playwright and its browser, SDKs, global tools). Both found in the Git pilot, where a lab wrote SSH keys to the real `~/.ssh` and Playwright was installed without asking.
- `docs/testing.md`: how the tests work (layers, fixtures, each file, how to add a test), linked from the README and CONTRIBUTING.
- README badges: tests, latest release and licenses; a "What's new" section links this file.
- How to update and remove the skill (FAQ, linked from the README's Install section), and the third-party licenses (Lucide icons, book photos) in the README.
- `docs/faq.md`: plans, cost, continuing a book, privacy, editing by hand, topics and languages, tested code, images.
- `images.py`: real images for the books. `search` and `fetch` find and download free-license photos (public domain, CC0, CC BY, CC BY-SA) from Wikimedia Commons; `screenshot` captures the book's application running (Playwright). Each image gets its line in `img/CREDITS.md` and a caption credit; `audit.py` reports a photo or screenshot without credit as an error.
- Donations: Pix (random key), Bitcoin and HiddenSwap QR codes in the README, and the GitHub Sponsor button.
- WSL 2 guide (`docs/integrations/wsl.md`): install WSL, Ubuntu and Claude Code inside it, so the skill tests Linux commands on Windows. The README recommends it, and the skill points to it once per book when Linux commands cannot run on native Windows.

### Changed

- Translations have their own folder in the library, `translated-books/<slug>-<lang>/` (before: next to the original), with its READMEs, its section in the lists and on the website, and the EPUB and site workflows watching it. `book.py brief` finds the original in `created-books/` or `improved-materials/`, and still next to the translation in older libraries.
- Images are chosen by context: SVG diagrams for what the reader cannot see (structure, logic, flow, states) and real images (photos, screenshots) for real things and scenes (a person, an application's screen, files open in an editor). The image choice is now `real` (the default) or `svg`; screenshots of desktop applications are asked of the user. Notion keeps only the SVG diagrams.

- Analogies: each chapter checks whether its central concept is abstract and, if so, gives it one analogy with the fixed label (`Analogia`/`Analogy`), the pairs and where it breaks. `audit.py` warns when a whole book has none (found by comparing the Docker Compose pilot, with zero analogies, with an older book).
- stem profile: teach the secure form first and say what the default exposes (for example, ports bound to `127.0.0.1`), and mention operating-system differences in behavior, not only in commands (WSL files under `/mnt/c`). The assessment's "Safety" line covers security risks for technology topics.
- Long books: after about 3 chapters, the skill suggests continuing in a new conversation, since each turn rereads the whole conversation (in the pilot, three chapters cost US$ 17.80 in a long conversation and US$ 5.16 in a new one).
- Create mode: the syllabus research compares the draft with 2 or 3 reference syllabi (official documentation, a popular course, a well-reviewed book) and the assessment shows the gaps and what was done with each. Eval case 3 checks it. Notes (missing tools, research links) now go before the assessment, so the message always ends with the invitation to say "approved".
- Google Drive guide: the connector is available on every plan (on Team and Enterprise an owner turns it on). Notion: the copy keeps only the SVG diagrams; photos and screenshots stay in the EPUB and the website (`notion.py` lists them in `left_out`). README: code execution must be on in the Claude app, and a line on tested code and real images.
- `SECURITY.md`: GitHub in Claude Code connects through `gh auth login`, not a connector; in Improve mode the original files stay private, and the improved book is published like any other.

### Removed

- The planned illustrations (`illustrate.py`, HTML templates and a paid image API) and the `illustrations` and `paid-api` image choices: real images replace them.
- The library leftovers at the root of this repository (`created-books/`, `improved-materials/`, `site/`, `library.yaml` and the `epub.yml` and `site.yml` workflows), from when it was also the library template. Libraries come from the [syllabook-library](https://github.com/Joshpcbrrj/syllabook-library) template.

## [0.3.0] - 2026-11-20

Research-first books, tested by behavior evals and four pilots (Docker Compose, English, guitar, history of computing).

### Added

- Behavior evals in `evals/` for `claude plugin eval`: eight cases (triggering, language, assessment + syllabus, adjustment, nothing before "approved", writing a chapter, improve mode, publishing without connections), run on the user's machine.
- A library template of its own, [syllabook-library](https://github.com/Joshpcbrrj/syllabook-library): each user creates their library from it with **Use this template**. `tools/sync_template.py` keeps it equal to the skill's library skeleton.

### Changed

- This repository is no longer a GitHub template: it holds the skill and its development files. The README, the GitHub guide and the Publish mode point to the library template instead.
- The skill follows its step checklists without showing them in the conversation.
- After a syllabus change, the reply starts with one line saying what changed, in the conversation language, followed by the whole syllabus.
- Chapters point to prerequisite books instead of teaching their content again, and each structure, flow or comparison gets a diagram.
- The images and reading choices are always asked, even when the user says to go straight to writing.
- Checkpoint and final zips are written outside the library repository, so they are never committed with the book.
- Research in English by default (most documentation and references), with sources in the book language when they are the best for the topic.
- Research dossiers: after approval, the skill opens every source and writes `research/c<nn>.md` for each chapter (facts with links and dates, examples, common mistakes, in the book language); `book.py brief` hands the chapter its dossier and `audit.py` warns when one is missing. Dossiers stay in the library but not in the EPUB, website or Notion.
- Fact checks open the source instead of dropping a claim, and every explanation of a command must match its real output.
- Each chapter is reread as a native reader of the book language before it is done; quality steps are never skipped to save tokens.
- Research dossiers are written for every chapter of the book before the first one, even when the user asks for only some chapters now.
- The assessment lists what the research still debates and, for physical skills, a safety line.
- Topic guide: the assessment shows "How this book teaches <topic>" (practice, checking yourself, pictures, what to avoid) for approval, and after approval it becomes `research/guide.md`, which adapts the area profile to the topic and goes to every chapter through `book.py brief`. Topics without a profile of their own get a method made for them.
- At most 3 questions before the syllabus, counting any question about the approach; anything else becomes a stated default.
- Music diagrams in `diagram.py`: `chord` (chord boxes with fingers, open and muted strings, barre and the first fret), `fretboard` (notes on the neck, the root highlighted) and `tab` (tablature with bar lines), for any tuning; each one also prints the same content as copyable text.

### Fixed

- `book.py validate` no longer stops with a traceback when the home folder is read-only (a sandbox): remembering the current book is skipped.
- `plugin.json` now says version 0.2.0 (it still said 0.1.0).

## [0.2.0] - 2026-11-20

Colorful, explicit diagrams.

### Added

- 104 Lucide icons (ISC license) embedded in the skill (`assets/icons.json`), drawn by name with `icon:`; `diagram.py --icons` lists them, and a misspelled name is reported with suggestions.
- `icon` and `note` (a smaller line under the bold text) in flow, layers, tree, timeline, sequence and compare boxes; `side_note`, `side_icon` and `side_color` for a flow decision's other way out.
- `scene`: a short row of icons joined by arrows, `+` or `=` (folder → files, A + B = C), as its own diagram type or inside a cheat-sheet card.
- `subtitle` for every diagram.
- README: the Syllabook icon, a banner in each language and a picture of the skill's first message in Claude Code.

### Changed

- Stronger theme: colored box backgrounds, a gradient underline under the title, contrast of at least 4.5:1 checked by the tests.
- Cheat sheets: an icon badge per card, drawn check marks (or an icon per item) and an optional scene under the items.
- `compare` with `style: wrong-right` draws its marks as icons instead of emoji, which depended on the reader's fonts; no diagram contains emoji now.
- A YAML syntax error in a spec shows the file and line instead of a Python traceback.
- The sample book's chapter 1 diagram is drawn from a spec (`img/_source/c01-lista.yaml`).

## [0.1.0] - 2026-11-20

First release of the rebuilt skill.

### Added

- Install instructions in the README (Claude app and Claude Code).

- Rebuild plan in `plano/` (in Portuguese), with the pilot evaluations and a draft of the new skill.
- New repository layout: `created-books/`, `improved-materials/`, `site/` and `docs/`.
- Community files: licenses (CC BY-SA 4.0 and MIT), code of conduct, contributing guide, security policy, issue and pull request templates.
- Documentation in English, with a Portuguese version of each page and a language switcher at the top.
- Docling installation guide in `docs/integrations/docling.md`.
- The new skill in `skills/syllabook/`: `SKILL.md`, the modes (Create, Improve, Translate, Publish), the references (teaching, book parts, sources, syllabus, visuals, examples, cover), the area profiles, the style guides (pt-BR, en) and the library skeleton. The scripts arrive in a later step.
- Kit tests (`tests/run.py`) and the "Kit tests" Action; translation checker (`tools/translation.py`); skill packager (`tools/package_skill.py`) and the "Skill release" Action, triggered by version tags.
- `.gitattributes`, so text files use LF line endings on every system.
- First scripts of the skill: `book.py` (validate `book.yaml` and the concept graph, chapter skeleton and brief, progress, status), `audit.py` (ready criteria per chapter and for the whole book) and `facts.py` (sentences to fact-check), with a sample book in `tests/fixtures/` and tests for each script.
- `build.py`: navigation between chapters, the book map, the concept index, the EPUB with answers moved to an appendix (links both ways), the zip in the repository layout (split above 100 files), a partial checkpoint zip, the library lists and the website source.
- The website is built with [Zensical](https://zensical.org/), the successor of Material for MkDocs: one search across every book, answers as collapsible blocks, code copy button and dark mode.
- Test suite rebuilt with pytest: one file per part of the kit, one case per validation and audit rule, branch coverage measured and required (95% or more), lint with Ruff, and CI on Windows and Linux with Python 3.10 and 3.12. Replaces `tests/run.py`.
- `diagram.py`: SVG diagrams from short YAML specs in the books' theme (flow, timeline, compare, boxes, layers, tree, sequence, bars, cards), sized by the reading profile, with fit checks and a contact sheet rendered to PNG.
- `projects.py`: projects assembled from the book's code blocks, evolved across chapters, run and checked against an expected output; paths that leave the project folder are refused.
- `ingest.py`: study materials (Markdown, folders of pages, HTML, web addresses, EPUB, DOCX, PDF, slides) converted to Markdown sections plus an outline, through Docling when available.
- `notion.py`: chapters, chapter 0, the mock exam, the glossary and the index page converted to Notion's format (answers as toggles, notes as callouts, SVG diagrams and real photos as uploads, illustrations left out).
- Integration guides for GitHub, Notion, Google Drive and GitHub Pages, in English and Portuguese, with the compatibility table checked against current documentation.
- Docling installers for Windows (`install/install-docling.ps1`) and macOS/Linux (`install/install-docling.sh`), with a tested helper that adds Docling to the Claude app's settings and keeps a backup.
- Plugin layout: the skill moved to `skills/syllabook/`, and `.claude-plugin/plugin.json` and `marketplace.json` make this repository a Claude Code plugin and marketplace (needed for `claude plugin eval`).
- Workflow checks: actionlint in CI, and `tests/test_workflows.py`, which runs the real steps of `epub.yml` and `site.yml` in a test library with fake `gh` and `pip`.
- Library workflows `epub.yml` and `site.yml` (in `assets/library/` and at the root of this template); they do nothing while there are no books.

### Changed

- The project is now called **Syllabook** (repository `syllabook`), and it is a GitHub template.
- `biblioteca.yaml` became `library.yaml`, with keys in English.

### Fixed

- `notion.py`: the chapter list on the index page was read by Notion as a numbered list inside each bullet and renumbered from 1 (chapter 0 showed as "1."); the numbers are now escaped and blocks are separated by blank lines. Found by publishing the sample book to a real Notion page.
- `projects.py`: on Windows with Python 3.13 or later, a path such as `/etc/passwd.py` was no longer refused, because `os.path.isabs` returns `False` for a rooted path without a drive.

### Removed

- The old skills `revisar-curso-biblioteca` and `criar-livro-tecnologia`, the scripts in `ferramentas/` and the tests, to be replaced by the new skill.
- The courses and books published with the old skills (they will be rebuilt with the new one), and the `epubs` and `skill` releases.

[Unreleased]: https://github.com/Joshpcbrrj/syllabook/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/Joshpcbrrj/syllabook/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Joshpcbrrj/syllabook/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Joshpcbrrj/syllabook/releases/tag/v0.1.0
