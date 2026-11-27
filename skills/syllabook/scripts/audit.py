#!/usr/bin/env python3
"""Ready criteria for a chapter or the whole book.

Usage:
  python scripts/audit.py <n> [--book B]   one chapter
  python scripts/audit.py [--book B]       the whole book (chapters, fixed parts, images)

Errors block (`ready: false`, exit code 1). Warnings are allowed, but go to the
final summary with the reason. Limits follow the reading profile in book.yaml.
"""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diagram
import illustration
from common import (READING, chapter_numbers, chapter_path, find_book, labels, load_yaml, out, placeholders,
                    research_path, slugify)

# blocks that hold program output or data, not code: no comment required
NO_COMMENT_LANGS = {'', 'text', 'txt', 'output', 'console', 'plaintext', 'json', 'csv', 'markdown', 'md', 'diff'}
COMMENT = re.compile(r'^\s*(#|//|--|/\*|\*|<!--|;|%|\'|"""|rem\b)', re.I)  # """: a Python docstring
FILLER = {
    'en': r'\b(?:simply|just|obviously|basically)\b',
    'pt': r'\b(?:simplesmente|obviamente|basicamente|é só)\b',
    'es': r'\b(?:simplemente|obviamente|básicamente)\b',
}
IMAGE = re.compile(r'!\[(.*?)\]\(([^)\s]+)\)')  # alt text may hold brackets: [7, 8, 9]
# a port published with no host address listens on every network interface (stem profile: secure by default)
OPEN_PORT = [re.compile(r'''^\s*-\s*["']?(\d+(?:-\d+)?:\d+(?:-\d+)?(?:/(?:tcp|udp))?)["']?\s*(?:#.*)?$'''),  # compose
             re.compile(r'''(?:\s-p|--publish)[ =]["']?(\d+(?:-\d+)?:\d+(?:-\d+)?)\b''')]  # docker run
YAML_LANGS = {'yaml', 'yml'}
LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s#]+\.md)(#[^)]*)?\)')


def audit_chapter(path, n, lab, limits, language, errors, warnings):
    name = os.path.basename(path)
    text = open(path, encoding='utf-8').read()
    lines = text.splitlines()

    def where(i):
        return f'{name}:{i}'

    if '<!-- TODO' in text:
        errors.append(f'{name}: {text.count("<!-- TODO")} TODO placeholder(s) left')
    required = ['In this chapter', 'Practice', 'Quick review', 'Summary', 'Sources']
    if n > 1:
        required.append('Where we left off')
    for part in required:
        if lab[part] not in text:
            errors.append(f'{name}: missing section "{lab[part]}"')

    for tag in dict.fromkeys(placeholders(text)):
        errors.append(f'{name}: "<{tag}>" outside code is read as an HTML tag: it disappears on GitHub and on the '
                      f'website and breaks the EPUB; write [{tag}] (TEACHING.md §7)')
    in_code, lang, start, commented = False, '', 0, False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('```'):
            if not in_code:
                in_code, lang, start, commented = True, stripped[3:].strip().lower(), i, False
            else:
                size = i - start - 1
                if lang not in NO_COMMENT_LANGS and size >= 4 and not commented:
                    errors.append(f'{where(start)}: {lang} block with {size} lines and no comment explaining why')
                in_code = False
            continue
        if in_code:
            if COMMENT.match(line) or re.search(r'\s(#|//|--)\s', line):
                commented = True
            if lang not in NO_COMMENT_LANGS:
                for rule in OPEN_PORT[:1] if lang in YAML_LANGS else OPEN_PORT[1:]:
                    m = rule.search(line)
                    if m:
                        warnings.append(f'{where(i)}: port {m.group(1)} is published on every network interface: '
                                        f'teach 127.0.0.1:{m.group(1)} first, or write 0.0.0.0 and say why it must '
                                        'be open')
            if len(line) > limits['code']:
                # real output, URLs and long unbreakable tokens cannot be wrapped honestly
                unbreakable = lang in NO_COMMENT_LANGS or '://' in line or max(map(len, line.split() or [''])) >= 40
                (warnings if unbreakable else errors).append(
                    f'{where(i)}: line with {len(line)} characters (limit {limits["code"]})')
            continue
        if stripped.startswith('<summary>') or stripped.lstrip('> ').startswith('<summary>'):
            if i < len(lines) and lines[i].lstrip('> ').strip():
                errors.append(f'{where(i)}: blank line needed after <summary>')
        if stripped.lstrip('> ') == '</details>' and i > 1 and lines[i - 2].lstrip('> ').strip():
            errors.append(f'{where(i)}: blank line needed before </details>')
        if stripped.startswith('|') and i < len(lines) and re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[i]):
            cols = len(re.findall(r'(?<!\\)\|', stripped)) - 1
            if cols > limits['columns']:
                warnings.append(f'{where(i)}: table with {cols} columns (limit {limits["columns"]})')
        for alt, target in IMAGE.findall(line):
            if not alt.strip():
                errors.append(f'{where(i)}: image without alt text ({target})')
            if not target.startswith('http') and not os.path.exists(os.path.join(os.path.dirname(path), target)):
                errors.append(f'{where(i)}: image not found ({target})')
        for target, _ in LINK.findall(line):
            if not target.startswith('http') and not os.path.exists(os.path.join(os.path.dirname(path), target)):
                errors.append(f'{where(i)}: link to a missing file ({target})')
        filler = FILLER.get(language.split('-')[0])
        if filler:
            prose = re.sub(r'`[^`]*`', '', line)
            for word in re.findall(filler, prose, re.I):
                warnings.append(f'{where(i)}: filler word "{word}"')
    if in_code:
        errors.append(f'{where(start)}: code block never closed')

    heading = re.search(rf'^##\s.*{re.escape(lab["Sources"])}.*$', text, re.M)
    sources = text[heading.end():].split('\n## ', 1)[0] if heading else ''
    if heading and 'http' not in sources:
        warnings.append(f'{name}: "{lab["Sources"]}" has no link')
    return re.findall(r'\]\(\.\./img/([^)\s]+)\)', text)


def uncredited(book_dir, names):
    """Photos and screenshots (raster images without a spec in img/_source/) with no credit line."""
    path = os.path.join(book_dir, 'img', 'CREDITS.md')
    credits = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
    for name in names:
        stem, ext = os.path.splitext(name)
        if ext.lower() not in ('.png', '.jpg', '.jpeg', '.gif', '.webp'):
            continue
        if glob.glob(os.path.join(book_dir, 'img', '_source', stem + '.*')) or name in credits:
            continue
        yield name


HEAVY_IMAGE = 1024 * 1024  # the site and the EPUB carry every image: a 4K screenshot weighs megabytes


def heavy(book_dir, names):
    """Images over 1 MB, with their size in MB."""
    for name in names:
        path = os.path.join(book_dir, 'img', name)
        if os.path.isfile(path) and os.path.getsize(path) > HEAVY_IMAGE:
            yield name, os.path.getsize(path) / 1024 / 1024


def illustrations(book_dir, names):
    """SVGs drawn by hand (no spec in img/_source/): the illustrations that illustration.py checks."""
    for name in names:
        stem, ext = os.path.splitext(name)
        path = os.path.join(book_dir, 'img', name)
        if ext.lower() == '.svg' and os.path.exists(path) and \
                not glob.glob(os.path.join(book_dir, 'img', '_source', stem + '.*')):
            yield name, path


COPY_WORDS = 12  # this many words in a row, the same as in the original, is a copy, not a short quotation


def prose_words(text):
    """The words of a Markdown text, outside code blocks, inline code and links: commands and sources may match,
    prose may not."""
    text = re.sub(r'^(`{3,}|~{3,}).*?^\1\s*$', ' ', text, flags=re.S | re.M)
    text = re.sub(r'`[^`\n]*`', ' ', text)
    text = re.sub(r'(?:https?://|www\.)[^\s<>()\[\]]+', ' ', text)
    return re.findall(r'\w+', text.lower())


def copied_from(original_dir, book_dir):
    """(file of the book, the copied words) for each run of COPY_WORDS words that also appears in the original."""
    seen = {}
    for path in glob.glob(os.path.join(original_dir, '**', '*.md'), recursive=True):
        words = prose_words(open(path, encoding='utf-8').read())
        for i in range(len(words) - COPY_WORDS + 1):
            seen.setdefault(tuple(words[i:i + COPY_WORDS]), True)
    found = []
    for path in sorted(glob.glob(os.path.join(book_dir, '**', '*.md'), recursive=True)):
        words = prose_words(open(path, encoding='utf-8').read())
        for i in range(len(words) - COPY_WORDS + 1):
            if tuple(words[i:i + COPY_WORDS]) in seen:
                found.append((os.path.relpath(path, book_dir).replace(os.sep, '/'), ' '.join(words[i:i + COPY_WORDS])))
                break
    return found


def book_on_one_page(book_dir, lab, readme, chapter0):
    """BOOK.md §4: the whole book as one cards diagram, in the README and at the start of chapter 0. Returns errors."""
    label = lab['The book on one page']
    m = re.search(rf'^## .*{re.escape(label)}\s*$(.*?)(?=^## |\Z)', readme, re.M | re.S)
    # the alt text may hold brackets of its own (code such as [7, 8, 9]): match up to "](img/"
    image = re.search(r'!\[.+?\]\((?:\./)?img/([^)\s]+\.svg)\)', m.group(1), re.S) if m else None
    if not image:
        return [f'README.md: no "{label}" section with its SVG (BOOK.md §4): one card per chapter, '
                'drawn with diagram.py (type cards) from a spec in img/_source/']
    name = image.group(1)
    errors = []
    spec = os.path.join(book_dir, 'img', '_source', os.path.splitext(name)[0] + '.yaml')
    if not os.path.exists(os.path.join(book_dir, 'img', name)):
        errors.append(f'README.md: img/{name} ("{label}") not found')
    elif not os.path.exists(spec) or (load_yaml(spec) or {}).get('type') != 'cards':
        errors.append(f'img/{name}: "{label}" must be drawn by diagram.py from a cards spec '
                      f'(img/_source/{os.path.basename(spec)})')
    if f'../img/{name}' not in chapter0:
        errors.append(f'chapter 0: "{label}" (img/{name}) missing near the start, so the EPUB and Notion have it too')
    return errors


def main():
    p = argparse.ArgumentParser(description='Ready criteria for a chapter or the whole book.')
    p.add_argument('n', type=int, nargs='?')
    p.add_argument('--book')
    p.add_argument('--original', help='an improved book: the folder ingest.py wrote the original to')
    args = p.parse_args()
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    language = data.get('language', 'en')
    lab = labels(language)
    reading = (data.get('choices') or {}).get('reading', 'large')
    limits = READING[reading]
    errors, warnings, used = [], [], set()

    numbers = [args.n] if args.n else chapter_numbers(data)
    for n in numbers:
        file = chapter_path(book_dir, n)
        if not file:
            errors.append(f'chapter {n}: file missing')
            continue
        names = audit_chapter(file, n, lab, limits, language, errors, warnings)
        used.update(names)
        for name in uncredited(book_dir, names):
            errors.append(f'chapter {n}: img/{name} is a photo or screenshot without a line in img/CREDITS.md')
        for name, mb in heavy(book_dir, names):
            warnings.append(f'chapter {n}: img/{name} has {mb:.1f} MB: shrink it to at most 1600 pixels wide')
        for name, svg in illustrations(book_dir, names):
            problems, notes = illustration.check(svg, diagram.PROFILES[reading]['width'])
            errors += [f'chapter {n}: img/{name}: {p}' for p in problems]
            warnings += [f'chapter {n}: img/{name}: {w}' for w in notes]
        ch = next((c for c in data['chapters'] if c['n'] == n), {})
        if not data.get('translation_of') and not os.path.exists(research_path(book_dir, n)):
            # a translation reuses the original's research; every other chapter is written from its dossier
            warnings.append(f'chapter {n}: no research dossier (research/c{n:02d}.md)')
        if data.get('origin') == 'improved' and not ch.get('sources_original'):
            errors.append(f'chapter {n}: does not say where it comes from in the original (sources_original)')

    if not args.n:
        files = [os.path.basename(f) for f in glob.glob(os.path.join(book_dir, 'chapters', '*.md'))]
        fixed = {'chapter 0': [f for f in files if f.startswith('00-')],
                 lab['Final mock exam']: [f for f in files if slugify(lab['Final mock exam']) in f],
                 lab['Glossary']: [f for f in files if slugify(lab['Glossary']) in f]}
        for part, found in fixed.items():
            if not found:
                errors.append(f'fixed part missing: {part}')
            else:
                text = open(os.path.join(book_dir, 'chapters', found[0]), encoding='utf-8').read()
                if '<!-- TODO' in text:
                    errors.append(f'{found[0]}: TODO placeholder(s) left')
                used.update(re.findall(r'\]\(\.\./img/([^)\s]+)\)', text))
        chapters = [open(f, encoding='utf-8').read() for f in glob.glob(os.path.join(book_dir, 'chapters', '*.md'))]
        if not any(f'**{lab["Analogy"]}:**' in text for text in chapters):
            # TEACHING.md §6: abstract new ideas get an analogy; a whole book without one usually skipped them
            warnings.append('no analogy in the whole book: check each chapter\'s central concept (TEACHING.md §6)')
        readme = os.path.join(book_dir, 'README.md')
        if not os.path.exists(readme):
            errors.append('README.md missing (the book front page)')
        else:  # the book's front page shows the book on one page
            front = open(readme, encoding='utf-8').read()
            used.update(re.findall(r'\]\((?:\./)?img/([^)\s]+)\)', front))
            zero = fixed['chapter 0']
            chapter0 = open(os.path.join(book_dir, 'chapters', zero[0]), encoding='utf-8').read() if zero else ''
            errors += book_on_one_page(book_dir, lab, front, chapter0)
        img = os.path.join(book_dir, 'img')
        if os.path.isdir(img):
            existing = {os.path.relpath(f, img).replace(os.sep, '/')
                        for f in glob.glob(os.path.join(img, '**', '*'), recursive=True)
                        if os.path.isfile(f) and '_source' not in f and not f.endswith('CREDITS.md')}
            for orphan in sorted(existing - used):
                warnings.append(f'image not used in any chapter: img/{orphan}')

    if args.original:
        for file, words in copied_from(args.original, book_dir):
            errors.append(f'{file}: text copied from the original ("{words}..."): '
                          'rewrite it in your own words or quote one short passage with its link')
    elif data.get('origin') == 'improved' and not args.n:
        warnings.append('improved book: before publishing, run audit.py --original <the folder ingest.py wrote> '
                        'to check that nothing of the original was copied (chapters, research, README)')

    out({'scope': f'chapter {args.n}' if args.n else 'whole book', 'ready': not errors,
         'errors': errors, 'warnings': warnings}, 0 if not errors else 1)


if __name__ == '__main__':
    main()
