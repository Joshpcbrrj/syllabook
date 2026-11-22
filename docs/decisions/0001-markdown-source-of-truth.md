# 1. Markdown is the source of truth

**English** | [Português](0001-markdown-source-of-truth.pt-BR.md)

**Status:** accepted · **Source:** `plano/PLANO.md §2, §8`

## Context

Books used to live in Notion, which is hard to version, test or publish elsewhere.

## Decision

Every book is a folder of Markdown files with a `book.yaml`, in a Git repository. The EPUB, the website and the Notion copy are built from it at the end.

## Consequences

Books can be tested, diffed and published for free (GitHub Pages and releases). Notion is a copy: edits made there do not come back to the book.
