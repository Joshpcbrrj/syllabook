# Mode 5: Review and update a book from the library

Follow this checklist. Track it yourself and never show it to the user: they see the results of each step, not the list.

```text
- [ ] 1. Identify the book
- [ ] 2. Diagnosis (nothing changes yet)
- [ ] 3. Review assessment, approved by the user
- [ ] 4. Fixes, chapter by chapter
- [ ] 5. Close the edition, build and publish
```

A review keeps the book's promise and brings it up to date: what is wrong is fixed, what aged is updated, what today's rules would catch is improved. It is not a rewrite: a book that needs a different audience, level or sequence is a new book (mode 1 or 4).

## 1. Identify the book

The user points to a book in their library (or sends its zip). Run `book.py status` on it: if it is not finished, this is mode 6 (continue), not a review. Read nothing else yet.

## 2. Diagnosis

Gather the findings before proposing anything:

1. `book.py review`: the edition, the review dates, the sources not reopened for a year, and the whole-book audit with **today's** rules (a book written before a rule existed shows here what it lacks).
2. **Reported errors:** the open issues of the library repository that name this book (with GitHub connected: `gh issue list --search "<title>"`; otherwise ask the user to paste them). Read each one; never take a report as true without checking it.
3. **What aged:** reopen each stale source and the official release notes since `reference_version`. Note what changed for the book's commands, options, defaults, prices, laws or facts.
4. **Running again:** `projects.py` and every command of the chapters, in the same order as when writing (`SKILL.md`, chapter loop step 3). An output that differs from the book is a finding.
5. **Scope × content:** with `book.py base`, compare the chapters' summaries with the goal and the promise: a topic promised and treated superficially, a concept used before it is explained, a summary that promises what the chapter does not deliver.
6. **What the user wants changed**, if they said it.

Work from the chapter files and the scripts' output; do not reread the whole book in the conversation.

## 3. Review assessment

One message, in the conversation language:

```text
🔎 Review of <title> (edition <x.y>, <date>)

Wrong (fix now):          <item → chapter, in one line each>
Out of date:              <item → chapter, what changed and since when>
Today's rules:            <what the current audit asks for → chapters>
Reported by readers:      <issue → verdict: confirmed / not confirmed>
Suggestions (optional):   <improvements that keep the promise>

Proposed edition: <x.y.z+1 for errata only | x.y+1 for fixes and small updates | x+1.0 when a new version of the tool or law changes the content>
Review again by: <YYYY-MM, sooner when the topic changes fast>

Say what to keep out, or "approved".
```

Nothing changes before "approved". What goes beyond the book's promise goes to its next steps, never into this edition.

## 4. Fixes, chapter by chapter

One chapter at a time, only the passages in the approved list:

1. Fix the passage; never rewrite a chapter to fix it.
2. Run what changed (code, commands, calculations), check new facts against the sources (`SOURCES.md` §5), update the source's `checked` date, reread the passage as a native reader and run `audit.py <n>`.
3. A fix that changes what the reader does or believes (a command that was wrong, a fact that changed) gets a short note right there, in the book language: `> ⚠️ **Fixed in edition <x.y>:** <what it said, what is right and why>`. Typos, links and wording need no note.
4. Record each change in `changes` (`SYLLABUS.md`), and reply in each confirmed issue with what was fixed (GitHub connected) or list them for the user.
5. If a fix changes what a chapter teaches, update its card in the book on one page (`BOOK.md` §4) and redraw it. A book written before that rule gets one now: the review audit lists it.
6. Long reviews follow the same economy as long books: after about 3 chapters, write the handoff note (`book.py handoff`) and suggest a new conversation.

## 5. Close the edition

1. `audit.py` on the whole book with no errors, then `book.py edition <x.y> --summary "<one or two lines>" --review-by <YYYY-MM>`: it records the edition, the review date and the history that `build.py` writes in the book's README.
2. If `reference_version` changed, update it in `book.yaml`.
3. `build.py` (EPUB and zip), then publish as in `modes/PUBLISH.md`: the library lists show the new edition and date; update the Notion copy too.
4. Final summary: what was fixed, what was updated, the issues answered, what stayed out and why, and the next review date.
