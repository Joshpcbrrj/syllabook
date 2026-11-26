# Profile: stem (programming, math, statistics, technology)

## Practice

- **Programming and technology:** a hands-on lab in every chapter (`🧪 Lab`), done step by step with the real output; the practice ladder with code to complete, to write and to change.
- **Running project (the default for programming, infrastructure and code):** one project that grows across the chapters, as in a real job (an API that gains a database, then a proxy, then a production setup). Each chapter's lab adds one step to it, and the final project closes it. Every step is a tutorial the reader can replicate alone: complete, copyable blocks with the file path in bold (`TEACHING.md` §5), the command to run, its real output and what to observe; at the end of the chapter, the files the project should now have and one command that checks it works. Exercises outside the project still practice each idea. Use a separate final project only when the topics share no natural project; say which in the syllabus.
- **Math and statistics:** worked examples with every step justified; exercises from mechanical to word problems; at least one proof or "why it works" per key result, at the reader's level; a final set of mixed problems.

## Verification

- Run every code block and every command; show the real output. If it cannot run in the session, follow the order in `SKILL.md` (user's computer, guided run, then "not run").
- `projects.py` assembles and runs the projects; the book is not delivered if a project fails.
- Math: redo every calculation, preferably with code (e.g. Python) in the session; check every proof step.

## Topic order

why it exists → definition → **predict** (ask the reader to predict the result) → example with real values → code or calculation with output → diagram → common mistake.

## Visuals

Flowcharts for control flow, trace tables for loops and recursion, boxes with values for memory and data structures, architecture blocks, sequence diagrams for protocols, function graphs and geometric figures.

## Cautions

- Pin the `reference_version` and `review_by` for tools that change.
- Mention the operating system when a command differs (Windows, macOS, Linux), with each variant tested or marked. Do the same when the **behavior** differs even with the same command: speed, file permissions, line endings, file-change events, paths (for example, files under `/mnt/c` in WSL are slower and do not send change events to containers).
- **Security by default:** when the topic exposes something (a port, a service, a file share, a token), teach the safe form first and say what the default exposes (for example, a published port opens on every address of the machine unless bound to `127.0.0.1`; `audit.py` warns about every port published with no address, and a port that must be open is written `0.0.0.0:` with the reason). Credentials never go in code, images or commits; services do not run as root without a reason.
- Formulas in LaTeX; never as images.
