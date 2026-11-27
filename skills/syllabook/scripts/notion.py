#!/usr/bin/env python3
"""Converts the book to Notion's Markdown, for the copy in Notion (modes/PUBLISH.md §4).

Usage:
  python scripts/notion.py <n> [--book B]      one chapter (0 = chapter 0; the mock exam has the next number)
  python scripts/notion.py <file.md> [--book B]  a file in chapters/ without a number, such as the glossary
  python scripts/notion.py index [--book B]    the book's index page
  python scripts/notion.py all --out <dir> [--book B]   every page, one file each, in reading order;
                                               prints only the list (title, file, size, uploads)

Prints JSON with `content` (ready for the Notion page tools) and `uploads`: the images to
upload first. Each upload has a `placeholder` that appears in the content as
<image source="PLACEHOLDER">; replace it with what the Notion upload tool returns.

What changes on the way:
  <details> answers      -> <toggle> (Notion saves <details> as plain text)
  > quotes and notes     -> <callout> with the note's emoji as the icon
  SVG diagrams           -> uploads
  photos and screenshots (PNG/JPG) -> left out: Notion gets the SVG diagrams only;
                            they stay in the EPUB and the site, and a line links to the chapter's page there
  inline code ending in \\   -> plain text (Notion would read "\\`" as an escaped backtick)
  links to other chapters -> plain text (the chapters are subpages in Notion)
  <!-- comments -->, navigation and the generated map -> removed
"""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import chapter_path, fail, find_book, first_h1, labels, load_yaml, out, site_url

IMAGE = re.compile(r'^!\[([^\]]*)\]\(\.\./img/([^)\s]+)\)\s*$')
CHAPTER_LINK = re.compile(r'\[([^\]]+)\]\((?!https?:)[^)\s]+\.md(#[^)\s]*)?\)')
COMMENT = re.compile(r'<!--.*?-->', re.S)
# inline code ending in a backslash: Notion reads "\\`" as an escaped backtick and the code never closes
TRAILING_BACKSLASH = re.compile(r'`([^`\n]*\\)`')
# the emoji a note starts with picks the callout's color
CALLOUT_COLORS = {'⚠️': 'yellow_bg', '💡': 'blue_bg', '🛠️': 'green_bg', '🔥': 'orange_bg', '❌': 'red_bg',
                  '✅': 'green_bg', '🔎': 'purple_bg', '🧪': 'blue_bg', '🎯': 'purple_bg'}
EMOJI = re.compile(r'^\s*(?:\*\*)?\s*([\U0001F300-\U0001FAFF☀-➿][️‍\U0001F300-\U0001FAFF]*)')


def strip_generated(text):
    for block in ('nav', 'map', 'index', 'list'):
        text = re.sub(rf'<!-- {block}:start -->.*?<!-- {block}:end -->', '', text, flags=re.S)
    return COMMENT.sub('', text)


def inline(text):
    """Text outside code blocks: inline code that ends in a backslash becomes plain, escaped text."""
    return TRAILING_BACKSLASH.sub(lambda m: m.group(1).replace('\\', '\\\\'), text)


def callout(lines):
    """A Markdown quote becomes a callout; its first emoji becomes the icon."""
    text = '\n'.join(re.sub(r'^>\s?', '', line) for line in lines).strip()
    m = EMOJI.match(text)
    icon = m.group(1) if m else '💬'
    if m:
        text = (text[:m.start(1)] + text[m.end(1):]).lstrip()
        text = re.sub(r'^\*\*\s+', '**', text)
    color = CALLOUT_COLORS.get(icon, 'gray_bg')
    return [f'<callout icon="{icon}" color="{color}">', inline(text), '</callout>']


def convert(text, book_dir, page_url='', see_label='See the image on the website'):
    """Returns (content, uploads, left_out). With page_url, a left-out image points to its page on the site."""
    lines = strip_generated(text).splitlines()
    result, uploads, left_out = [], [], []
    i, fence = 0, None
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # code blocks pass through untouched, whatever they contain
        if fence:
            result.append(line)
            if stripped.startswith(fence):
                fence = None
            i += 1
            continue
        m = re.match(r'^(`{3,}|~{3,})', stripped)
        if m:
            fence = m.group(1)
            result.append(line)
            i += 1
            continue
        if stripped == '<details>':
            j, summary, body = i + 1, '', []
            while j < len(lines) and lines[j].strip() != '</details>':
                s = re.match(r'^\s*<summary>(.*?)</summary>\s*$', lines[j])
                if s and not summary:
                    summary = s.group(1).strip()
                else:
                    body.append(lines[j])
                j += 1
            inner, more_uploads, more_left = convert('\n'.join(body), book_dir, page_url, see_label)
            uploads += more_uploads
            left_out += more_left
            # an answer starting with "4." would become a numbered list item
            inner = re.sub(r'^(\d+)\.(\s|$)', r'\1\\.\2', inner.strip())
            result += ['<toggle>', summary, '', inner, '</toggle>']
            i = j + 1
            continue
        if stripped.startswith('>'):
            j = i
            while j < len(lines) and lines[j].strip().startswith('>'):
                j += 1
            quoted = lines[i:j]
            # a quote holding an answer: keep the answer as a toggle after the callout
            if any('<details>' in q for q in quoted):
                plain = [re.sub(r'^\s*>\s?', '', q) for q in quoted]
                k = next(n for n, q in enumerate(plain) if q.strip() == '<details>')
                result += callout(['> ' + q for q in plain[:k] if q.strip()])
                inner, more_uploads, more_left = convert('\n'.join(plain[k:]), book_dir, page_url, see_label)
                uploads += more_uploads
                left_out += more_left
                result.append(inner.strip())
            else:
                result += callout(quoted)
            i = j
            continue
        img = IMAGE.match(stripped)
        if img:
            alt, name = img.groups()
            if not name.lower().endswith('.svg'):
                # Notion keeps the SVG diagram standard; photos and screenshots stay in the EPUB and the site
                left_out.append(name)
                if page_url:
                    result.append(f'🖼️ *{alt}* · [{see_label}]({page_url})')
            else:
                placeholder = f'UPLOAD:{name}'
                uploads.append({'placeholder': placeholder, 'file': os.path.join(book_dir, 'img', name),
                                'kind': 'svg'})
                result.append(f'<image source="{placeholder}">{alt}</image>')
            i += 1
            continue
        result.append(inline(CHAPTER_LINK.sub(r'\1', line)))
        i += 1
    content = re.sub(r'\n{3,}', '\n\n', '\n'.join(result)).strip() + '\n'
    return content, uploads, left_out


def title_of(text):
    return first_h1(text)


def chapter_url(book_dir, data, file):
    """The chapter's page on the library website, or '' when the book is not in a library on GitHub."""
    from build import collection, library_settings
    settings, _ = library_settings(book_dir)
    site = site_url(settings.get('repository', ''))
    if not site:
        return ''
    name = os.path.splitext(os.path.basename(file))[0]
    return f'{site}{collection(data)}/{data["slug"]}/chapters/{name}/'


def index_page(book_dir, data):
    """The book's index page in Notion: what it is, the links, and the chapter list."""
    from build import collection, epub_url, library_settings
    settings, _ = library_settings(book_dir)
    lab = labels(data.get('language', 'en'))
    repo = settings.get('repository', '')
    folder = collection(data)
    links = []
    if repo:
        site = site_url(repo)
        tree = f'https://github.com/{repo}/tree/{settings.get("branch", "main")}'
        links += [f'🌐 [{lab["Book map"]}]({site}{folder}/{data["slug"]}/)',
                  f'📂 [GitHub]({tree}/{folder}/{data["slug"]})',
                  f'📥 [{lab["Download EPUB"]}]({epub_url(settings, data["slug"])})']
    parts = []
    if data.get('subtitle'):
        parts.append(data['subtitle'])
    if links:
        parts.append('\n'.join(['<callout icon="📚" color="blue_bg">', '\n'.join(links), '</callout>']))
    # "- 0. x" would be a numbered list inside the bullet, and Notion renumbers it from 1
    chapters = [f'0\\. {lab["How to study this book"]}'] + [f'{c["n"]}\\. {c["title"]}' for c in data['chapters']]
    items = [f'- {c}' for c in chapters + [lab['Final mock exam'], lab['Glossary']]]
    parts += [f'## {lab["Chapters"]}', '\n'.join(items)]
    # Notion's Markdown wants a blank line between blocks
    return {'title': data['title'], 'content': '\n\n'.join(parts) + '\n', 'uploads': [], 'left_out': []}


def page(book_dir, data, file):
    """One file of chapters/ as a Notion page: title, content, uploads, left_out."""
    text = open(file, encoding='utf-8').read()
    content, uploads, left_out = convert(text, book_dir, chapter_url(book_dir, data, file),
                                         labels(data.get('language', 'en'))['See the image on the website'])
    # the title becomes the Notion page title, not a heading inside the page
    title = title_of(text)
    if title and content.startswith(f'# {title}'):
        content = content[len(f'# {title}'):].lstrip('\n')
    return {'title': title, 'content': content, 'uploads': uploads, 'left_out': left_out}


def whole_book(book_dir, data, out_dir):
    """Every page in reading order, each written to its own file; prints only the list, never the text."""
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(book_dir, 'chapters', '*.md')))  # numbered first, then the glossary
    parts, left_out = [], []
    for k, (name, part) in enumerate([('index', index_page(book_dir, data))] +
                                     [(os.path.basename(f), page(book_dir, data, f)) for f in files]):
        target = os.path.join(out_dir, f'{k:02d}-{os.path.splitext(name)[0]}.md')
        with open(target, 'w', encoding='utf-8', newline='\n') as f:
            f.write(part['content'])
        parts.append({'title': part['title'], 'file': target, 'chars': len(part['content']),
                      'uploads': part['uploads']})
        left_out += part['left_out']
    out({'parent_first': parts[0]['title'], 'parts': parts, 'left_out': left_out,
         'note': 'create the index page first, then the other parts under it, several per create call, '
                 'in this order; read each file only when you send it'})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('target', help='a chapter number, "index" or "all"')
    p.add_argument('--book')
    p.add_argument('--out', help='with "all": the folder for one file per page (outside the library)')
    args = p.parse_args()
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    if args.target == 'index':
        out(index_page(book_dir, data))
    if args.target == 'all':
        if not args.out:
            fail('"all" needs --out <folder>: a temporary folder outside the library')
        whole_book(book_dir, data, args.out)
    if args.target.endswith('.md'):
        file = os.path.join(book_dir, 'chapters', os.path.basename(args.target))
        if not os.path.exists(file):
            fail(f'not found: chapters/{os.path.basename(args.target)}')
    elif args.target.isdigit():
        file = chapter_path(book_dir, int(args.target))
        if not file:
            fail(f'chapter {args.target} has no file yet')
    else:
        fail('give a chapter number, a file in chapters/, "index" or "all"')
    out(page(book_dir, data, file))


if __name__ == '__main__':
    main()
