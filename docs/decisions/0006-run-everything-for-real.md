# 6. Every command runs for real

**English** | [Português](0006-run-everything-for-real.pt-BR.md)

**Status:** accepted · **Source:** `plano/PLANO.md §21`

## Context

A book with a command that does not work loses the trust of someone studying alone, who has no teacher to ask.

## Decision

Every piece of code and every command is run, in this order: in the session; on the user's computer, if it is linked to the app; guided run (the user runs it and pastes the output); otherwise it is marked "not run" with a warning.

## Consequences

Books show real outputs, and what could not run is visible in the text and in the final summary. Labs that touch credentials run with a temporary home folder.
