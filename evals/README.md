# Behavior evals

Cases for `claude plugin eval`: each one sends a real request to Claude with the Syllabook plugin loaded and grades what it does. They run on your machine, on your own Claude account (each run costs about US$ 0.10 to 0.60), never in CI.

| Case | Checks |
| --- | --- |
| `01-acionamento` | the skill is triggered by a study request |
| `02-idioma` | it talks in the user's language (English here) |
| `03-parecer-ementa` | assessment + syllabus in one message, nothing written yet (no "book on one page" either) |
| `04-ajuste` | an adjustment returns the whole syllabus, renumbered |
| `05-nada-antes-do-aprovado` | no chapter before "aprovado" |
| `06-escrever-capitulo` | writes chapter 2 of an approved book (needs a shell: Linux, macOS or WSL) |
| `07-aprimorar` | improve mode: the material's promise and an improvement plan |
| `08-publicar-sem-conexoes` | publishing path without GitHub or Notion |
| `09-proximo-livro-direcoes` | option 4: offers directions from the earlier book's next steps, no level question |
| `10-proximo-livro-ementa` | option 4: a syllabus that starts where the earlier book ended and does not reteach it |
| `11-revisar` | option 5: review assessment, a wrong reader report is not taken as true, nothing changes before approval |
| `12-projeto-continuo` | a programming syllabus names one running project that the chapters build step by step |
| `13-traduzir` | option 3: a term table and adaptation notes first, nothing created before approval |
| `14-publicar-livro-pronto` | option 6: a finished book from its unzipped folder is validated, audited and built into an EPUB (needs a shell) |
| `15-continuar` | option 7: `book.py status` first, and the handoff note shown before anything else (needs a shell) |
| `16-perfil-idiomas` | languages profile: research-backed assessment (input, output, spaced repetition), CEFR "can do" goals |
| `17-perfil-conhecimento` | knowledge profile: reference sources, legends to check, fact × interpretation × legend |

Every start option has at least one case: 1 (03–06, 12), 2 (07), 3 (13), 4 (09, 10), 5 (11), 6 (08, 14), 7 (15), and every area profile: stem (03, 12), skills (05), languages (16), knowledge (17). Cases that need a shell are tagged `completo` and use `scaffold.sh` with the sample book of the tests (`tests/fixtures/sample-book`).

## Running

From the repository root. The short cases (tag `curto`) need no shell, so they also run on Windows:

```bash
claude plugin eval . --tag curto --runs 2 --scaffold --allow-tools Write WebSearch WebFetch --judge-model opus --trust-plugin --no-publish --max-cost-usd 10 --threshold 0
```

Add `--model sonnet` (or `haiku`) to check that the instructions hold with the models people use: the skill recommends Sonnet for the chapters, and the free plan uses it.

`Write` must be granted (`--allow-tools Write`), or every case that lists it is refused. Cases 03 and 10 also need `WebSearch` and `WebFetch`: without them the skill rightly refuses to build a syllabus from memory, since it must research in the session. To run some cases only, `--case` takes one glob (the last `--case` wins and `{a,b}` is not supported): `--case "*proximo*"` runs 09 and 10.

Cases with a `scaffold.sh` (06, 13, 14, 15) need `--scaffold` to prepare the book, and the scaffold runs only where `bash` takes Linux paths (WSL, Linux or macOS; on Windows it fails with exit 127). A WSL distro with Docker Desktop's integration turned on has `~/.docker/contexts` as a link to Windows, and the eval then refuses every case that grants Bash; `evals/wsl-eval.sh` runs the eval with a temporary `HOME` that links only Claude Code's own files, so those cases run there too:

```bash
wsl -e bash -lc "'/mnt/d/<path to the repo>/evals/wsl-eval.sh' --tag completo --runs 1 --ablation none --scaffold --allow-tools Bash Write Edit --judge-model opus --trust-plugin --no-publish --max-cost-usd 10 --threshold 0"
```

In these cases the sandbox keeps the workspace read-only for the shell: a script that writes (`build.py`, `book.py done`) fails there, so the graders accept a reply that says so and gives the command instead of working around it. Cases 06, 14 and 15 (tag `completo`) grant Bash, which the eval refuses on Windows (no sandbox there), so run them in WSL, Linux or macOS:

```bash
claude plugin eval . --tag completo --runs 1 --ablation none --scaffold \
  --allow-tools Bash Write Edit --judge-model opus --trust-plugin --no-publish --max-cost-usd 10 --threshold 0
```

Notes:

- Each case also runs once without the plugin (the "without" arm) to show the difference; `--ablation none` skips it.
- Use the Opus judge (`--judge-model opus`). On 2026-11-26 the Sonnet judge failed, three votes out of three, replies that met every item of long criteria (cases 03, 16 and 17), and the Opus judge passed them; Haiku, the default, is noisier still. The judge costs little next to the runs.
- In case 6 the sandbox may make the shell read-only in the workspace: the skill then writes the chapter with its file tools, or stops and explains, both acceptable. Read the run's last message before judging a low score.
- Results go to `evals/results/` (ignored by git); `report.html` there shows every reply and grader verdict.
