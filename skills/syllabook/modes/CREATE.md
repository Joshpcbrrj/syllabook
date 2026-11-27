# Mode 1: Create, from topic to approved syllabus

The sections below follow this checklist, step by step. Track it yourself and never show it to the user: they see the results of each step, not the list.

```text
- [ ] 1. Understand the request (up to 3 questions)
- [ ] 2. Pick the area profile
- [ ] 3. Research
- [ ] 4. Assessment + syllabus (in the same message)
- [ ] 5. Adjust until "approved"
- [ ] 6. Save book.yaml and follow the flow in SKILL.md
```

**No chapter before "approved".** A wrong syllabus costs the whole book; adjusting it costs one message.

## Contents

1. Understand the request
2. Area profile
3. Research
4. Assessment + syllabus
5. Adjust until "approved"
6. Save and continue
7. The next book in a track (mode 4)

## 1. Understand the request

One message, **at most 3 questions in total**, and only what the request did not say. Every question counts, including one about the approach (chronological or by theme, which style, which instrument): if a fourth seems useful, pick a sensible default for it, say it in one line and let the user change it later.

| Question | Default if the user does not answer |
| --- | --- |
| What is your level in this topic today? | never studied it |
| Why do you want to learn it? (e.g. work, travel, hobby, exam) | general use |
| Size: short guide (5–6 ch.), book (8–12) or complete (13–16)? | book |

Do not ask how much time per day: chapter 0 offers schedules at three paces.

In the same message, offer (not a required question): "If you have books, PDFs, EPUBs or a Google Drive folder on this topic, send them: I'll use them as sources." If the user sends any, run each file through `ingest.py` and use only its outline until step 3. In Google Drive, list the files found and let the user choose before opening any. Usage rules are in `references/SOURCES.md` (understand and check, never copy).

If the user has a library on GitHub, check `created-books/`, `improved-materials/` and `translated-books/` for a book on the same topic. If there is one, show what it covers and ask: expand it, write the next book in the track (§7), or take another angle.

## 2. Area profile

Pick the profile from the topic and read only that one (at most 2 when the topic combines areas, e.g. electronics = `skills.md` + `stem.md`):

| Profile | Topics |
| --- | --- |
| `stem.md` | programming, math, statistics, technology |
| `languages.md` | English and other languages |
| `skills.md` | music, electronics, drawing, cooking, hands-on work |
| `knowledge.md` | history, sciences, concepts, reading topics |

The profile is the starting point, not the whole method: the research (§3) finds how **this** topic is learned and practiced, and that becomes the book's topic guide (§4), which adapts the profile. A topic that fits no profile well (chess, cooking, photography, law) still gets its own method this way.

## 3. Research

Follow `references/SOURCES.md` (search in English by default, §2). The goal of the research, and nothing beyond it:

- the **usual curriculum** for the topic (university syllabi, textbooks, official documentation);
- the **prerequisites** and the **common mistakes and myths** of beginners;
- **how this topic is learned and practiced** by people who learn it well: the kind of practice with evidence behind it, how a self-learner can check their own answer without a teacher, the pictures that explain it best, and the safety risks (for technology topics: what is insecure by default);
- the **current version**, when the topic changes over time (tools, laws);
- **2 or 3 reference syllabi** to compare against: the table of contents of the official documentation, a popular course and a well-reviewed book (or the ones the user sends). For each topic they teach that the draft syllabus lacks, decide: add it, leave it for "Next steps", or leave it out on purpose (outdated, bad practice, belongs to another book). Compare coverage and order only: never copy their structure or text, and never use a copy of unclear origin as a source;
- 4 to 8 reliable **sources**, each with the date it was checked.

Start with the user's materials, if any (only the useful sections, by the outline). Search with specific questions and stop when you have the above. The sources go into `book.yaml`; chapters reuse them and do not research the topic again.

## 4. Assessment + syllabus

Before showing it, save the draft **outside the repository** (`<temp>/book-<slug>.yaml`, with `approved_on: ""`, the `sources` and the concept graph; the model is in `references/SYLLABUS.md`) and run `python scripts/book.py validate /tmp/book-<slug>.yaml`. Fix it until it passes.

Show it in one message, in this format. Labels go in the conversation language; titles in the book language. Any note (a tool missing in this session, how the labs will run, the research links) goes **before** the 🔎 block: the message always ends with the invitation to adjust and to say "approved".

```text
🔎 Assessment: <topic>
What it is and what it is for: <1–2 sentences>
Helps to know first: <prerequisites, or "nothing">
How people usually learn it: <the usual path, in 1–2 sentences>
Common mistakes and myths: <2–3 items, including what the research still debates>
Safety: <physical skills: injury, tools, electricity · technology: what is exposed by default, credentials, privileges · otherwise leave the line out>
Main sources: <2–4 names>
Compared with: <the 2–3 reference syllabi> · Gaps: <topics they teach that this book adds, leaves for later or leaves out, and why; or "none">

🧭 How this book teaches <topic>
Practice: <the kind of practice, in one line>
Checking yourself: <how the reader knows they got it right>
Pictures: <the diagrams that help most>
Avoid: <what does not work for this topic>

📘 <Title> · <start level> → <end level> · <n> chapters · ~<h> h
For whom: <one sentence>
When you finish, you will: <the book's goal, checkable>
Prerequisites: <knowledge or books>

0. How to study this book
1. <Title>                     → <goal with an action verb>
2. ...
n. <Final project or challenge> → <what the reader delivers>
   Final mock exam

Next steps: <2–4 later books, each with why and its main topics>
Reference version: <only if the topic changes over time, with the date>

Adjust freely: "longer", "shorter", "drop 5", "add X",
"merge 3 and 4", "swap the order", "more hands-on".
When it looks right, say "approved".
```

Syllabus rules:

- **Beginner to intermediate**, unless the user asks otherwise.
- **Progression:** each chapter uses only concepts from earlier ones (`book.py validate` checks the concept graph).
- **One goal per chapter**, starting with a verb (never a list of commands or topics), with verbs that can be checked ("build", "translate", "play at 80 bpm"), never "understand" or "know", not even as one of several verbs ("understand, resolve and avoid conflicts" becomes "resolve a merge conflict and avoid the common ones"). The same holds for the book's goal ("When you finish, you will"). Weak verbs and rewrites: `references/SYLLABUS.md`, "Goals". `book.py validate` warns about them: fix every warning before showing the syllabus; without code execution, check each goal yourself.
- **Chapter 0 is one line** ("0. How to study this book"; you may add in parentheses what it holds). The book on one page, the placement test and the other fixed parts are written at the end (`references/BOOK.md`): never put their content in the syllabus message.
- **Chapter 1 delivers a concrete win** (something that works, is said or is played on day one).
- **Practice in every chapter**, of the kind defined by the profile. For programming, infrastructure or code, the chapters build one **running project** (`areas/stem.md`): name it in the 🧭 block ("Practice: one project that grows, [what it is]"), and end each hands-on chapter line with the step it adds to that project, by name ("5. Loops → repeat a task for each item of a list; project: total the sales of every file"), so the reader sees the project grow chapter by chapter.
- **Explicit scope:** what does not fit goes to "Next steps".

## 5. Adjust until "approved"

Read requests in plain language. Always reply with **one line** saying what changed, in the conversation language (e.g. "Mudou: ..."), as the **very first line** of the message (nothing before it, not even "Here is the revised syllabus"), then **the whole updated syllabus**. Anything else you want to suggest goes after the syllabus, briefly. The reply always has this shape:

```text
<Changed, in the conversation language>: <what changed, in one line>

<the whole syllabus, in the §4 format>

<at most 2 short suggestions, only if needed>
``` Run `book.py validate` after every change.

| Request | What to do |
| --- | --- |
| "longer" / "more complete" | add or deepen chapters without breaking the progression; state the new total |
| "shorter" | merge nearby chapters; the rest goes to Next steps |
| "drop X" | remove it; if a later chapter depends on it, move the minimum it needs there and say so in the "changed" line |
| "add Y" | fit it where the progression allows; if Y is too advanced for the level, suggest leaving it for another book |
| "more hands-on" | turn explanation goals into tasks; make the final project measurable |
| "merge", "split", "swap the order" | do it and check that no chapter now uses a concept not yet taught |
| a request that conflicts with the level or size | do it, and state the effect in one sentence |

## 6. Save and continue

When you hear "approved" (or a clear equivalent in any language), and only then:

1. Fill in `approved_on` and save to `created-books/<slug>/book.yaml` (with GitHub connected, on the `draft/<slug>` branch).
2. Follow "Flow after approval" in `SKILL.md`, from step 1.

**Next steps in `book.yaml`:** save each one as `{title, why, topics}` (2–4 topics). They become the last chapter's next steps (`build.py` writes them) and the starting point of the book that continues this one (§7).

**Changes after approval:** show the impact ("dropping ch. 5 affects the examples in ch. 6 and 8"), ask approval for that change only, and update `book.yaml` as described in `references/SYLLABUS.md`.

## 7. The next book in a track (mode 4)

The user points to a book in their library ("my Docker book") and wants a book that goes further. It is mode 1 with a head start:

1. Run `book.py base <slug or folder>`: the earlier book in short (level, goal, concepts, chapter summaries, next steps, and which steps already have a book). Do not open its chapters; the summary is enough. If it is a translation, the script gives its original.
2. Offer 2–4 directions in one short message: its next steps that have no book yet (with their why and topics), plus "or tell me what you want to go deeper into". If the user already said it, skip this.
3. Steps 1–5 of this mode as usual, but: no question about level or what the user already knows (the earlier book answers it); the research looks only at the new ground; the syllabus never reteaches what the earlier book's concepts cover, only reviews it in chapter 0 and in warm-ups.
4. If the book starts a new track, add the track's display name to `tracks` in `library.yaml` (`SYLLABUS.md`). In the new `book.yaml`, from `for_the_new_book`: `level.start` = the earlier book's end level, `prerequisites: [<earlier slug>]`, the same `track` with the next `order`, and `continues: {book: <earlier slug>, step: <n>}` (no `step` when the idea came from the user). Concepts from the earlier book are written `<slug>:<concept id>` in `depends`; `book.py validate` checks them.
5. Keep what the reader already knows: the same terms (the earlier glossary), the same style and, when it fits, the same running project, now growing further.
6. The placement test says who can skip the earlier book and points to it for whoever cannot.
7. Once approved, run `book.py link`: the earlier book's next step now points to this book, and its last chapter links here on its next build.
