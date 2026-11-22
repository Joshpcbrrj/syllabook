---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [curto]
---

Quero revisar o meu livro "Docker Compose na prática" (está pronto e publicado na minha biblioteca do Syllabook). Nesta conversa estou sem shell e sem GitHub conectado, então rodei eu mesmo `python scripts/book.py review --book created-books/docker-compose-na-pratica`:

```json
{
 "title": "Docker Compose na prática",
 "edition": "1.3.1",
 "reviewed_on": "2026-11-21",
 "review_by": "2027-05",
 "due": false,
 "reference_version": "Docker Compose v5.7.0, Docker Engine 29.9.3",
 "stale_sources": [],
 "audit": {
  "errors": [],
  "warnings": []
 },
 "next": "read the reported errors (issues on the library repository), reopen the stale sources, run projects.py and the chapters' commands again, then show the review assessment (modes/REVIEW.md)"
}
```

Um leitor abriu esta issue na biblioteca:

> **#7 Cap. 7 está errado sobre volumes.** O livro diz que `docker compose down` mantém os volumes nomeados, mas aqui eu rodei o down e meu banco sumiu. O certo é dizer que o down apaga os volumes.

Não tenho outras mudanças em mente.
