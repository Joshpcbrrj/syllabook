"""Shared helpers for the Syllabook scripts.

Finding the book: every script accepts `--book <folder or book.yaml>`. Without it,
it uses the SYLLABOOK_BOOK environment variable, then the current folder if it
holds a book.yaml, then the book selected by the last successful
`book.py validate` (saved in ~/.syllabook/current, or SYLLABOOK_STATE).
"""
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import unicodedata

# JSON output carries emoji and accents; Windows consoles default to another encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# the skill's version, sent in problem reports (report.py); "-dev" while CHANGELOG.md has unreleased changes
VERSION = '0.4.3-dev'
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.environ.get('SYLLABOOK_STATE') or os.path.join(os.path.expanduser('~'), '.syllabook', 'current')

# limits per reading profile (references/VISUALS.md §3)
READING = {'large': {'code': 80, 'columns': 6}, 'small': {'code': 60, 'columns': 4}}
# a map to the sources, never a source itself (SOURCES.md §1)
ENCYCLOPEDIA = re.compile(r'https?://(?:[\w-]+\.)*(wikipedia\.org|britannica\.com)\b', re.I)


def need_yaml():
    try:
        import yaml
    except ImportError:
        # the claude.ai sandbox can install from PyPI; quiet so the output stays short
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'pyyaml'], check=True)
        import yaml
    return yaml


def pandoc_path():
    """pandoc on the PATH, or the copy that comes with the pypandoc_binary package."""
    import shutil
    found = shutil.which('pandoc')
    if found:
        return found
    try:
        import pypandoc
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'pypandoc_binary'], check=True)
        import pypandoc
    return pypandoc.get_pandoc_path()


def load_yaml(path):
    yaml = need_yaml()
    with open(path, encoding='utf-8') as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            # a short message with the line instead of a traceback (e.g. an unquoted "?" in a value)
            mark, name = getattr(e, 'problem_mark', None), os.path.basename(path)
            if mark is None:
                fail(f'{name}: {e}')
            fail(f'{name} line {mark.line + 1}: {getattr(e, "problem", None) or e}')


def save_yaml(path, data):
    text = need_yaml().safe_dump(data, allow_unicode=True, sort_keys=False, width=100)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=1))
    sys.exit(code)


def fail(message):
    out({'ok': False, 'error': message}, 1)


# the HTML a book may hold in its Markdown; any other <word> outside code is a placeholder such as <sua resposta>,
# which GitHub and the website hide as an unknown tag and which makes the EPUB's XHTML invalid
HTML_TAGS = {'a', 'abbr', 'b', 'br', 'code', 'details', 'div', 'em', 'figcaption', 'figure', 'hr', 'i', 'img', 'kbd',
             'li', 'mark', 'ol', 'p', 'picture', 'pre', 's', 'small', 'source', 'span', 'strong', 'sub', 'summary',
             'sup', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'u', 'ul'}
TAG = re.compile(r'<(/?)([^<>\s/!][^<>\n]*?)>')
INLINE_CODE = re.compile(r'(`+)[^`\n]*?\1')


def is_placeholder(inner):
    first = re.split(r'[\s/]', inner, maxsplit=1)[0].lower()
    # an autolink (<https://...>, <mailto:...>) or an e-mail address is not a placeholder either
    return not (first in HTML_TAGS or re.match(r'[a-z][a-z0-9+.-]*:', first) or '@' in first)


def outside_code(text, change):
    """Applies change(segment) to the Markdown outside fenced blocks and inline code; returns the new text."""
    out, fence = [], None
    for line in text.split('\n'):
        stripped = line.strip().lstrip('> ').lstrip()
        m = re.match(r'(`{3,}|~{3,})', stripped)
        if fence:
            fence = None if m and stripped.startswith(fence) else fence
            out.append(line)
            continue
        if m:
            fence = m.group(1)
            out.append(line)
            continue
        parts, last = [], 0
        for code in INLINE_CODE.finditer(line):
            parts += [change(line[last:code.start()]), code.group(0)]
            last = code.end()
        out.append(''.join(parts) + change(line[last:]))
    return '\n'.join(out)


def placeholders(text):
    """The <placeholders> written outside code."""
    found = []
    outside_code(text, lambda s: found.extend(m.group(2) for m in TAG.finditer(s) if is_placeholder(m.group(2))) or s)
    return found


def escape_placeholders(text):
    """<sua resposta> -> &lt;sua resposta&gt; outside code, so every reader sees it."""
    return outside_code(text, lambda s: TAG.sub(
        lambda m: f'&lt;{m.group(1)}{m.group(2)}&gt;' if is_placeholder(m.group(2)) else m.group(0), s))


CONNECTORS = {'a', 'o', 'e', 'as', 'os', 'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no', 'nas', 'nos', 'com',
              'por', 'para', 'um', 'uma', 'y', 'del', 'la', 'el', 'en', 'con', 'an', 'the', 'of', 'and', 'to',
              'in', 'on', 'for', 'with'}


def slugify(text, limit=48):
    ascii_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_text.lower()).strip('-')
    if len(slug) > limit:
        # cut at a word boundary so file names stay readable
        slug = slug[:limit].rsplit('-', 1)[0]
        # nor end on "de", "the"...: "linha-de" reads as a broken name
        while '-' in slug and slug.rsplit('-', 1)[1] in CONNECTORS:
            slug = slug.rsplit('-', 1)[0]
    return slug


def labels(language):
    """Fixed labels of a book language, read from references/style/<language>.md."""
    def parse(lang):
        path = os.path.join(SKILL, 'references', 'style', f'{lang}.md')
        if not os.path.exists(path):
            return None
        text = open(path, encoding='utf-8').read().split('## Fixed labels', 1)[-1]
        rows = re.findall(r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$', text, re.M)
        return {part: label for part, label in rows if part not in ('Part', '---')}
    found = parse(language) or parse(language.split('-')[0])
    return found or parse('en')


def site_url(repository):
    """The library's GitHub Pages address (https://<owner>.github.io/<name>/), or '' without a repository."""
    if not repository or '/' not in repository:
        return ''
    owner, name = repository.split('/', 1)
    return f'https://{owner.lower()}.github.io/{name}/'


def remember(book_yaml):
    """Saves the current book for the next commands; a read-only home (a sandbox) only loses the shortcut."""
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, 'w', encoding='utf-8') as f:
            f.write(os.path.abspath(book_yaml))
    except OSError:
        pass


def find_book(arg=None):
    """Returns (book folder, book.yaml path) or stops with an error."""
    candidates = [arg, os.environ.get('SYLLABOOK_BOOK'), os.getcwd()]
    if os.path.exists(STATE):
        candidates.append(open(STATE, encoding='utf-8').read().strip())
    for c in candidates:
        if not c:
            continue
        path = c if c.endswith('.yaml') else os.path.join(c, 'book.yaml')
        if os.path.exists(path):
            return os.path.dirname(os.path.abspath(path)), os.path.abspath(path)
    fail('book not found: pass --book <folder>, or run "book.py validate <book.yaml>" first')


def first_h1(text):
    """The first '# ' heading outside code blocks (a '# comment' in Python code is not a title), or ''."""
    fence = None
    for line in text.splitlines():
        m = re.match(r'^\s*(`{3,}|~{3,})', line)
        if m and (fence is None or m.group(1).startswith(fence)):
            fence = None if fence else m.group(1)
        elif fence is None and line.startswith('# '):
            return line[2:].strip()
    return ''


COLLECTION_FOLDERS = ('created-books', 'improved-materials', 'translated-books')


def library_root(start):
    """The library repository (the folder with library.yaml) that holds start, or None."""
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, 'library.yaml')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def library_book(root, slug):
    """The folder of the book with this slug in the library, or None."""
    for folder in COLLECTION_FOLDERS:
        path = os.path.join(root, folder, slug)
        if os.path.exists(os.path.join(path, 'book.yaml')):
            return path
    return None


def library_slugs(root):
    return sorted(name for folder in COLLECTION_FOLDERS if os.path.isdir(os.path.join(root, folder))
                  for name in os.listdir(os.path.join(root, folder))
                  if os.path.exists(os.path.join(root, folder, name, 'book.yaml')))


def next_steps(data):
    """next_steps as dicts {step, title, why, topics[, book]}: plain strings (older books) become titles."""
    steps = []
    for i, s in enumerate(data.get('next_steps') or [], 1):
        s = {'title': s} if isinstance(s, str) else dict(s)
        steps.append({'step': i, 'title': s.get('title', ''), 'why': s.get('why', ''),
                      'topics': s.get('topics') or [], **({'book': s['book']} if s.get('book') else {})})
    return steps


def review_due(data, today=None):
    """True when review_by (YYYY-MM) is in the past: the book should be reviewed (modes/REVIEW.md)."""
    month = (today or datetime.date.today()).strftime('%Y-%m')
    return bool(data.get('review_by')) and str(data['review_by']) < month


def chapter_path(book_dir, n):
    found = sorted(glob.glob(os.path.join(book_dir, 'chapters', f'{n:02d}-*.md')))
    return found[0] if found else None


def research_path(book_dir, n):
    """The chapter's research dossier: notes with the facts, links and checked dates (SOURCES.md §2)."""
    return os.path.join(book_dir, 'research', f'c{n:02d}.md')


def chapter_numbers(data):
    return [c['n'] for c in data.get('chapters', []) if isinstance(c, dict) and 'n' in c]

