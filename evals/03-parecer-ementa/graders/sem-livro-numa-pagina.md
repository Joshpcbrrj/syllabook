---
type: regex
# The book on one page is a fixed part made at the end (BOOK.md §4): the syllabus must not carry it as a block
# of its own (a heading or bold title). Naming it in chapter 0's line ("0. Como estudar este livro (inclui o
# livro numa página)") is right.
pattern: "(^|\\n)\\s*(#+|\\*\\*|📄|🗺️)[^\\n]*[Ll]ivro numa p[áa]gina"
match: not_contains
---
