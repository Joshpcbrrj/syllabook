# 3. One chapter at a time, without agents

**English** | [Português](0003-segmented-chat-no-agents.pt-BR.md)

**Status:** accepted · **Source:** `plano/PLANO.md §2, §20`

## Context

Writing a book costs a lot of tokens, and the owner wants it to fit a regular subscription. Anthropic measured that an agent uses about 4 times, and a multi-agent system about 15 times, the tokens of a chat; and the chapters of a book depend on each other, the case where several agents work badly.

## Decision

The book is written one chapter at a time, in order, with a compact brief and the text saved to files. No agents or parallel chapters. After about three chapters, the skill suggests a new conversation and leaves a handoff note in `book.yaml`.

## Consequences

Each chapter starts from the brief and the previous summary, not from the whole conversation. A long book spans several conversations, and nothing is lost between them.
