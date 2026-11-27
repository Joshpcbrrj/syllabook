# Tutorial: your first book

**English** | [Português](tutorial.pt-BR.md)

In this tutorial you create a book from a topic, from the first message to the published website. The example is a real book: [Docker Compose na prática](https://joshpcbrrj.github.io/biblioteca-syllabook/), 14 chapters, written with Syllabook in November 2026. The real book is in Portuguese; here its titles are translated into English. The messages below show the shape of what Syllabook says, not a transcript, and your book's text will be different.

## Contents

- [Before you start](#before-you-start)
- [1. Ask for the book](#1-ask-for-the-book)
- [2. Answer up to three questions](#2-answer-up-to-three-questions)
- [3. Read the assessment and the syllabus](#3-read-the-assessment-and-the-syllabus)
- [4. Adjust until it looks right](#4-adjust-until-it-looks-right)
- [5. Approve and choose images and reading](#5-approve-and-choose-images-and-reading)
- [6. Follow the chapters](#6-follow-the-chapters)
- [7. Continue in a new conversation](#7-continue-in-a-new-conversation)
- [8. Publish](#8-publish)
- [What you have at the end](#what-you-have-at-the-end)

## Before you start

- **Syllabook installed** in the Claude app or in Claude Code: see [Install](../README.md#install). In Claude Code, turn on auto-update for the `syllabook` marketplace there, so new versions arrive by themselves; in the Claude app, upload the new zip at each release.
- **Optional:** GitHub and Notion connected ([integrations](integrations/README.md)). Without them you still get the whole book as a zip; Syllabook asks again at the end.
- For a technology book, Claude Code gives better results: it runs the commands on your computer. On Windows, use it inside [WSL 2](integrations/wsl.md).

## 1. Ask for the book

Say what you want to learn, in your own words and in your language:

```text
I want to learn Docker Compose. I already use docker run, but I want to bring up a project with an API and a database.
```

Syllabook confirms the language in one line ("I'll talk and write the book in English. Want to change either?"). If the request is not clear, it shows its menu of seven options; option 1 is "Create a book from a topic".

## 2. Answer up to three questions

It asks only what your request did not say, at most three questions: your level today, why you want to learn it, and the size (short guide, book or complete). Each has a default, so a short answer is enough:

```text
I use docker run at work. A book, not too long.
```

It also offers to use your own books, PDFs or a Google Drive folder as sources. You can skip it.

## 3. Read the assessment and the syllabus

Syllabook researches the topic (official documentation, two or three reference syllabi, the usual mistakes) and answers in one message. It starts with an assessment: what the topic is, what helps to know first, common mistakes, safety, the main sources, and how the book will teach it. Then comes the syllabus:

```text
📘 Docker Compose in practice · beginner → intermediate · 14 chapters · ~10 h
For whom: who already runs containers with docker run and wants to bring up a project with several services

0. How to study this book
1. Why one file for the project      → rebuild a long docker run as a compose.yaml
2. Install and check Compose         → check the plugin on Docker Desktop and on Linux
3. First compose.yaml                → bring up, list, read logs and take down with up, ps, logs and down
...
14. Final project: a complete stack  → API, database and proxy, for dev and production, with one command
    Final mock exam

Adjust freely: "longer", "shorter", "drop 5", "add X", "merge 3 and 4"...
When it looks right, say "approved".
```

Nothing is written yet. Each chapter has one goal you can check, and no chapter uses a concept that a later one teaches.

## 4. Adjust until it looks right

Ask for changes in plain language:

```text
Merge 11 and 12, and add a chapter about limits of CPU and memory.
```

Every reply starts with one line saying what changed, followed by the whole updated syllabus. Repeat until you like it. Changing the syllabus costs one message; a wrong syllabus would cost the whole book.

## 5. Approve and choose images and reading

```text
approved
```

Syllabook saves the syllabus in `book.yaml` and asks two short questions, with defaults:

- **Images:** SVG diagrams plus real images where they show it better (photos with a free license, screenshots), or SVG diagrams only.
- **Reading:** large screens, or a small black-and-white e-reader (narrower diagrams and code lines).

## 6. Follow the chapters

Syllabook first writes the research notes for every chapter, then the chapters, one at a time. For each one it writes the text, runs every command and piece of code, checks the facts against the sources, rereads it as a native reader and runs the audit. You see one line per chapter:

```text
✅ Ch. 3/14: First compose.yaml
```

When a command needs your computer (Docker, for example) and the session cannot run it, Syllabook gives you the commands, you run them and paste only the lines it asks for. If you prefer not to, the command is marked "not run" in the book.

## 7. Continue in a new conversation

Every message rereads the whole conversation, so after about three chapters Syllabook suggests a new one to save your usage limit. Nothing is lost: the progress is in `book.yaml`. Open a new conversation and say:

```text
continue my book Docker Compose na prática
```

If a usage limit runs out in the middle of a chapter, wait for it to reset and continue in the same chat.

## 8. Publish

After the last chapter, Syllabook writes the fixed parts (chapter 0, placement test, cheat sheets, mock exam, glossary), audits the whole book, makes the cover, the EPUB and a zip, and publishes:

- **With GitHub:** to your library repository; GitHub Actions build the website and the EPUB.
- **With Notion:** a copy of every chapter under the page you choose.
- **Without connections:** the zip, with the same folders as a library, and the steps to upload it.

The final summary lists the links, what was not run and why, and the suggested next books.

## What you have at the end

```text
created-books/docker-compose-na-pratica/
├── book.yaml      the syllabus, your choices and the progress
├── README.md      the book map, with links to every chapter
├── chapters/      00-como-estudar-este-livro.md ... 14-projeto-final-stack-completa.md, mock exam, glossary
├── img/           diagrams and images, with img/CREDITS.md
├── research/      the research notes, with the sources and the dates checked
└── projects/      the code of the projects, assembled from the chapters
```

Plus the [website with search](https://joshpcbrrj.github.io/biblioteca-syllabook/) and the EPUB in the library's `epubs` release.

**Next:** go deeper with the next book of the track ("create the next book from my Docker Compose book"), or review the book later ("review my Docker Compose book"). The fields of `book.yaml` are in the [reference](reference.md).
