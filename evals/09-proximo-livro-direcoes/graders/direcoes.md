---
type: llm
---

The user asked what the next book should be, continuing "Git e GitHub essencial". Pass if the reply does all of
this: (a) it is in Portuguese; (b) it offers at least two of the earlier book's next steps as options, by name
(GitHub Actions; git bisect and worktree; signed commits; Conventional Commits and semantic versioning); (c) it
asks the user to choose, or to say another topic they want to go deeper into; (d) it does not ask about the
reader's level or what they already know. Recommending one option, or combining some of them into one book, is
fine; so are an estimated size, a possible title, a note about connections (GitHub, Notion) and the model tip.
Fail only if it skips the choice and presents a full chapter-by-chapter syllabus, if it asks the reader's level
or prior knowledge, or if it ignores the earlier book's next steps.
