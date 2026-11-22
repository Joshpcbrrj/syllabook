# 10. Problem reports only with the user's yes

**English** | [Português](0010-problem-reports-with-consent.pt-BR.md)

**Status:** accepted · **Source:** `plano/V1.md §1b`

## Context

When the skill trips on a problem of its own, its maintainers only learn about it if someone reports it; but a report must never carry the user's data or be sent behind their back.

## Decision

The skill notes its own problems and, at the final summary, shows a report built by `report.py` (personal data removed). It is sent as an issue only after a clear yes, with the user's GitHub login or as a link they click. No automatic pull requests: fixes are made in the repository, with tests.

## Consequences

Reports reach the public Syllabook repository. A fork that changes the address receives the reports itself.
