# Behavior evals

Cases for `claude plugin eval`: each one sends a real request to Claude with the Syllabook plugin loaded and grades what it does. They run on your machine, on your own Claude account (each run costs about US$ 0.10 to 0.60), never in CI.

| Case | Checks |
| --- | --- |
| `01-acionamento` | the skill is triggered by a study request |
| `02-idioma` | it talks in the user's language (English here) |
| `03-parecer-ementa` | assessment + syllabus in one message, nothing written yet |
| `04-ajuste` | an adjustment returns the whole syllabus, renumbered |
| `05-nada-antes-do-aprovado` | no chapter before "aprovado" |
| `06-escrever-capitulo` | writes chapter 2 of an approved book (needs a shell: Linux, macOS or WSL) |
| `07-aprimorar` | improve mode: the material's promise and an improvement plan |
| `08-publicar-sem-conexoes` | publishing path without GitHub or Notion |
| `09-proximo-livro-direcoes` | option 4: offers directions from the earlier book's next steps, no level question |
| `10-proximo-livro-ementa` | option 4: a syllabus that starts where the earlier book ended and does not reteach it |
| `11-revisar` | option 5: review assessment, a wrong reader report is not taken as true, nothing changes before approval |

## Running

From the repository root. The short cases (tag `curto`) need no shell, so they also run on Windows:

```bash
claude plugin eval . --tag curto --runs 2 --allow-tools Write --judge-model sonnet --trust-plugin --no-publish --max-cost-usd 10 --threshold 0
```

`Write` must be granted (`--allow-tools Write`), or every case that lists it is refused. To run some cases only, `--case` takes one glob (the last `--case` wins and `{a,b}` is not supported): `--case "*proximo*"` runs 09 and 10.

Case 6 grants Bash, which the eval refuses on Windows (no sandbox there), so run it in WSL, Linux or macOS. It needs `--scaffold` to prepare the book:

```bash
claude plugin eval . --case 06-escrever-capitulo --runs 1 --ablation none --scaffold \
  --allow-tools Bash Write Edit --judge-model sonnet --trust-plugin --no-publish --max-cost-usd 6 --threshold 0
```

Notes:

- Each case also runs once without the plugin (the "without" arm) to show the difference; `--ablation none` skips it.
- The Sonnet judge (`--judge-model sonnet`) is stricter about the criteria and less noisy than the default Haiku.
- In case 6 the sandbox may make the shell read-only in the workspace: the skill then writes the chapter with its file tools, or stops and explains, both acceptable. Read the run's last message before judging a low score.
- Results go to `evals/results/` (ignored by git); `report.html` there shows every reply and grader verdict.
