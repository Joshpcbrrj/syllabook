#!/usr/bin/env python3
"""Lists the sentences of a chapter that state checkable facts.

Usage:  python scripts/facts.py <n> [--book B]
        python scripts/facts.py --fixed [--book B]   each item of chapter 0, the mock exam and the glossary,
                                                      with the chapter it points to

A sentence is listed when it has a year or date, a number with a unit or a
percentage, a quotation, or a proper name in the middle of the sentence (names the chapter
repeats 3 times or more are its subject, such as Linux or Git, and are not listed).
Code blocks are skipped (code is verified by running it). Check each
sentence against the sources (references/SOURCES.md §5).
"""
import argparse
import glob
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import chapter_numbers, chapter_path, fail, find_book, load_yaml, out

PATTERNS = {
    'date': re.compile(r'\b(1[0-9]{3}|20[0-9]{2})\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b'),
    # (?!\w) instead of \b: "%" is not a word character, so \b would never match after it
    'number': re.compile(r'\b\d+([.,]\d+)?\s?'
                         r'(%|por cento|percent|km|kg|mb|gb|tb|mhz|ghz|hz|v|w|ms|s|min|h|bpm|x)(?!\w)', re.I),
    'quote': re.compile(r'[“"«][^”"»]{12,}[”"»]'),
    # a capitalized word that does not start the sentence: likely a person, place or product
    'name': re.compile(r'(?<=[a-zà-ÿ,;:)] )[A-ZÀ-Ý][\w-]+'),
}
TOPIC_NAME = 3  # a name this many times in the chapter is the chapter's subject
MARKUP = re.compile(r'`[^`]*`|!\[.*?\]\([^)]*\)|\]\([^)]*\)|<[^>]+>|[*_#>|]')


def sentences(text):
    """Yields (line number, sentence) outside code blocks."""
    in_code = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith('```') or line.lstrip().startswith('~~~'):
            in_code = not in_code
            continue
        # headings and table separators state no facts
        if in_code or not line.strip() or line.lstrip().startswith('#') or re.match(r'^\s*\|?[\s:|-]+\|?\s*$', line):
            continue
        # entries of the Sources list are the references themselves, not claims
        if re.match(r'^\s*[-*]\s*\[[^\]]+\]\(https?://', line):
            continue
        # each table cell starts a new sentence, so its first word is not taken for a name
        clean = MARKUP.sub(' ', line.replace('|', '. '))
        for s in re.split(r'(?<=[.!?])\s+', clean):
            s = ' '.join(s.split())
            if len(s) > 15:
                yield i, s


CHAPTER_LINK = re.compile(r'\]\((\d{2})-[^)\s]*\.md[^)]*\)')


def items(text):
    """(line, text, chapter) of each item of a fixed part: a list entry, a paragraph, or a question with its hidden
    answer (the answer holds the link to the chapter). Headings and the blocks build.py writes are skipped."""
    text = re.sub(r'<!-- (\w+):start -->.*?<!-- \1:end -->', '', text, flags=re.S)
    blocks, in_details = [], False  # [line, [lines]]: paragraphs and list entries
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip().lstrip('>').strip()
        if stripped.startswith('#'):
            blocks.append([i, []])
            continue
        if stripped.startswith('<details>'):
            in_details = True
            # the hidden answer belongs to the question before it, a blank line apart
            if blocks and blocks[-1][1] and not blocks[-1][1][-1].strip():
                blocks[-1][1].pop()
            blocks[-1][1].append(line) if blocks else blocks.append([i, [line]])
            continue
        if stripped.startswith('</details>'):
            in_details = False
            continue
        if in_details:
            blocks[-1][1].append(line)
        elif not stripped:
            if blocks and blocks[-1][1] and blocks[-1][1][-1].strip():
                blocks[-1][1].append('')  # a blank line closes the paragraph, unless an answer follows
        elif re.match(r'^\s*[-*]\s', line) or not blocks or not blocks[-1][1] or not blocks[-1][1][-1].strip():
            blocks.append([i, [line]])
        else:
            blocks[-1][1].append(line)
    found = []
    for start, lines in blocks:
        joined = ' '.join(' '.join(MARKUP.sub(' ', re.sub(r'^\s*[-*]\s+', '', b)).split()) for b in lines if b.strip())
        if len(joined) > 15:
            links = CHAPTER_LINK.findall('\n'.join(lines))
            found.append((start, joined, int(links[0]) if links else None))
    return found


def fixed_parts(book_dir):
    """Chapter 0, the mock exam and the glossary: every file in chapters/ that is not a numbered chapter, plus
    00-*.md. A mock exam numbered after the last chapter (11-simulado-final.md) counts too."""
    files = sorted(glob.glob(os.path.join(book_dir, 'chapters', '*.md')))
    data = load_yaml(os.path.join(book_dir, 'book.yaml')) or {}
    numbers = {f'{n:02d}' for n in chapter_numbers(data)}
    return [f for f in files if os.path.basename(f)[:2] not in numbers]


def main():
    p = argparse.ArgumentParser(description='List the sentences with facts to check.')
    p.add_argument('n', type=int, nargs='?')
    p.add_argument('--fixed', action='store_true',
                   help='list each item of chapter 0, the mock exam and the glossary with its chapter')
    p.add_argument('--book')
    args = p.parse_args()
    book_dir, _ = find_book(args.book)
    if args.fixed:
        parts = []
        for path in fixed_parts(book_dir):
            listed = [{'line': line, 'chapter': ch, 'text': t[:300]}
                      for line, t, ch in items(open(path, encoding='utf-8').read())]
            parts.append({'file': os.path.relpath(path, book_dir).replace(os.sep, '/'), 'items': listed})
        out({'to_check': sum(len(p['items']) for p in parts), 'parts': parts,
             'note': 'Open the chapter each item points to and find where it says the same thing, with the same '
                     'date and the same doubt; an item with no chapter is checked against the chapter it comes '
                     'from. Fix the item, never the chapter (BOOK.md: the fixed parts teach nothing new).'})
    if args.n is None:
        fail('give a chapter number, or --fixed for chapter 0, the mock exam and the glossary')
    path = chapter_path(book_dir, args.n)
    if not path:
        fail(f'chapter {args.n} has no file yet')
    found = []
    listed = list(sentences(open(path, encoding='utf-8').read()))
    # a name the chapter repeats is its subject (Linux, Ubuntu, Git), not a claim to check: only rarer names count
    seen = Counter(w for _, s in listed for w in PATTERNS['name'].findall(s))
    for line, s in listed:
        kinds = [k for k, rx in PATTERNS.items() if k != 'name' and rx.search(s)]
        if any(seen[w] < TOPIC_NAME for w in PATTERNS['name'].findall(s)):
            kinds.append('name')
        if kinds:
            found.append({'line': line, 'kinds': kinds, 'sentence': s[:220]})
    out({'chapter': args.n, 'to_check': len(found), 'sentences': found})


if __name__ == '__main__':
    main()
