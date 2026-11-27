#!/usr/bin/env python3
"""The book's contract and memory: validate book.yaml, brief a chapter, record progress.

Usage:
  python scripts/book.py validate <book.yaml>     check fields and the concept graph; selects the book
  python scripts/book.py brief <n> [--book B]     create the chapter skeleton and print its brief
  python scripts/book.py reread <n> [--book B]    print the chapter's prose for the native reread, then a code
  python scripts/book.py done <n> --summary "..." --reread <code> [--book B]   record the chapter as done
  python scripts/book.py status [--book B]        where the book stopped and the next step
  python scripts/book.py handoff ["item"...] [--book B]   save what the next conversation must know (none = clear)
  python scripts/book.py base <slug-or-folder> [--library L]   summary of a library book to plan the next one
  python scripts/book.py link [--book B]          mark, in the earlier book, the next step this book continues
  python scripts/book.py review [--book B]        diagnosis for a review: audit with today's rules, old sources, dates
  python scripts/book.py edition <x.y> --summary "..." [--review-by YYYY-MM] [--book B]   close a reviewed edition

Prints JSON. Exit code 1 when something blocks the next step.
"""
import argparse
import datetime
import json
import os
import re
import secrets
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (chapter_numbers, chapter_path, fail, find_book, labels, library_book, library_root,
                    library_slugs, load_yaml, next_steps, out, remember, research_path, review_due, save_yaml,
                    slugify)

REQUIRED = ['title', 'slug', 'origin', 'language', 'profiles', 'level', 'audience', 'goal',
            'sources', 'approved_on', 'concepts', 'chapters']
PROFILES = {'stem', 'languages', 'skills', 'knowledge'}
# images: real = SVG diagrams plus real images (photos, screenshots) where they show it better; svg = diagrams only
CHOICES = {'images': {'real', 'svg'}, 'reading': {'large', 'small'}}
LABEL_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
CONCEPT_FIELDS = ('id', 'name', 'chapter', 'depends')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
NOTION_URL = re.compile(r'^https://([\w-]+\.)?notion\.(so|site|com)/\S+$')
MONTH_RE = re.compile(r'^\d{4}-\d{2}$')
EDITION_RE = re.compile(r'^\d+\.\d+(\.\d+)?$')  # 1.3 for a review, 1.3.1 for errata only
STALE_DAYS = 365  # a source not reopened for a year is checked again in a review
# goals must be checkable (references/SYLLABUS.md); these openings are not
WEAK_GOALS = re.compile(r'^(understand|know|learn about|be familiar|entender|compreender|conhecer|saber|'
                        r'aprender sobre|comprender|conocer)\b', re.I)
TODO = '<!-- TODO'


def validate(path):
    if not os.path.exists(path):
        fail(f'file not found: {path}')
    data = load_yaml(path)
    errors, warnings = [], []
    for key in REQUIRED:
        if key not in data:
            errors.append(f'missing field: {key}')
    if errors:
        return data, errors, warnings

    if not LABEL_RE.match(str(data['slug'])):
        errors.append('slug: use lowercase ASCII letters, digits and hyphens')
    if data['origin'] not in ('created', 'improved'):
        errors.append('origin: must be "created" or "improved"')
    profiles = data['profiles'] or []
    if not profiles or not set(profiles) <= PROFILES or len(profiles) > 2:
        errors.append(f'profiles: 1 or 2 of {sorted(PROFILES)}')
    if not isinstance(data['level'], dict) or not {'start', 'end'} <= set(data['level']):
        errors.append('level: needs start and end')
    for key, allowed in CHOICES.items():
        value = (data.get('choices') or {}).get(key)
        if value is not None and value not in allowed:
            errors.append(f'choices.{key}: must be one of {sorted(allowed)}')

    if not data['sources']:
        warnings.append('sources: empty')
    for i, s in enumerate(data['sources'] or [], 1):
        if not isinstance(s, dict) or not s.get('title') or not s.get('url'):
            errors.append(f'sources[{i}]: needs title and url')
        elif not DATE_RE.match(str(s.get('checked', ''))):
            errors.append(f'sources[{i}] "{s["title"]}": checked must be a YYYY-MM-DD date')

    chapters = data['chapters'] or []
    numbers = chapter_numbers(data)
    if numbers != list(range(1, len(chapters) + 1)):
        errors.append('chapters: n must go 1, 2, 3... in order, with no gaps')
    for ch in chapters:
        n = ch.get('n', '?')
        for key in ('title', 'goal'):
            if not ch.get(key):
                errors.append(f'chapter {n}: missing {key}')
        if ch.get('goal') and WEAK_GOALS.match(str(ch['goal']).strip()):
            warnings.append(f'chapter {n}: goal starts with a verb that cannot be checked ("{ch["goal"]}")')
        if not ch.get('topics'):
            warnings.append(f'chapter {n}: no topics')
        if not isinstance(ch.get('minutes'), int) or ch['minutes'] <= 0:
            warnings.append(f'chapter {n}: minutes missing (needed for the study schedule)')
        if data['origin'] == 'improved' and not ch.get('sources_original'):
            warnings.append(f'chapter {n}: sources_original empty (where it comes from in the original)')

    track_rules(path, data, errors, warnings)
    concepts = data['concepts'] or []
    taught = {}
    for c in concepts:
        cid = c.get('id', '')
        if not LABEL_RE.match(str(cid)):
            errors.append(f'concept "{cid}": id must be lowercase ASCII with hyphens')
        elif cid in taught:
            errors.append(f'concept "{cid}": listed twice')
        if c.get('chapter') not in numbers:
            errors.append(f'concept "{cid}": chapter {c.get("chapter")} does not exist')
        for key in [k for k in c if k not in CONCEPT_FIELDS]:
            # {id: x, name: gerenciadores (nvm, SDKMAN, uv)}: inside braces a comma starts a new field
            errors.append(f'concept "{cid}": unknown field "{key}" (fields: {", ".join(CONCEPT_FIELDS)}); '
                          'a name with commas inside {...} is split: write the name in quotes')
        taught[cid] = c.get('chapter')
    for c in concepts:
        for dep in c.get('depends') or []:
            if ':' in str(dep):
                other_book_concept(path, data, c.get('id'), dep, errors, warnings)
            elif dep not in taught:
                errors.append(f'concept "{c.get("id")}": depends on unknown concept "{dep}"')
            elif isinstance(taught[dep], int) and isinstance(c.get('chapter'), int) and taught[dep] > c['chapter']:
                errors.append(f'concept "{c["id"]}" (ch. {c["chapter"]}) depends on "{dep}", '
                              f'taught later (ch. {taught[dep]})')
    for n in numbers:
        if n not in taught.values():
            warnings.append(f'chapter {n}: teaches no concept in the concept graph')

    if data['origin'] == 'improved':
        if not data.get('original'):
            errors.append('improved book: missing original (what the material was)')
        promise = data.get('promise') or {}
        if not {'goal', 'audience', 'level', 'sequence'} <= set(promise):
            errors.append('improved book: promise needs goal, audience, level and sequence')
        pct = data.get('new_content_pct')
        if isinstance(pct, (int, float)) and pct > 20:
            warnings.append(f'new content at {pct}%: above the ~20% limit, say why in the plan')
    if data.get('translation_of') and not data.get('glossary'):
        errors.append('translation: missing glossary')
    for key, rule, form in (('reviewed_on', DATE_RE, 'a YYYY-MM-DD date'), ('review_by', MONTH_RE, 'a YYYY-MM month')):
        if data.get(key) and not rule.match(str(data[key])):
            errors.append(f'{key}: must be {form}')
    if data.get('notion_url') and not NOTION_URL.match(str(data['notion_url'])):
        errors.append('notion_url: must be the link of the book page in Notion (https://www.notion.so/...)')
    for i, e in enumerate(data.get('editions') or [], 1):
        if not isinstance(e, dict) or not all(e.get(k) for k in ('edition', 'date', 'summary')):
            errors.append(f'editions[{i}]: needs edition, date and summary')
    handoff = data.get('handoff')
    if handoff is not None and (not isinstance(handoff, list)
                                or not all(isinstance(h, str) and h.strip() for h in handoff)):
        errors.append('handoff: must be a list of sentences (what is pending for the next conversation)')
    if data['approved_on'] and not DATE_RE.match(str(data['approved_on'])):
        errors.append('approved_on: must be empty or a YYYY-MM-DD date')
    return data, errors, warnings


def track_rules(path, data, errors, warnings):
    """next_steps, prerequisites, track and continues: what links this book to the others."""
    for i, s in enumerate(data.get('next_steps') or [], 1):
        if isinstance(s, dict):
            if not s.get('title'):
                errors.append(f'next_steps[{i}]: needs a title')
            if 'topics' in s and not isinstance(s['topics'], list):
                errors.append(f'next_steps[{i}]: topics must be a list')
        elif not isinstance(s, str):
            errors.append(f'next_steps[{i}]: a title or {{title, why, topics}}')
    prerequisites = data.get('prerequisites') or []
    if not isinstance(prerequisites, list):
        errors.append('prerequisites: must be a list (slugs of earlier books, or plain text)')
        prerequisites = []
    track = data.get('track')
    if track is not None and (not isinstance(track, dict) or not track.get('name')
                              or not isinstance(track.get('order'), int)):
        errors.append('track: needs name and order (a whole number)')
    continues = data.get('continues')
    if continues is not None:
        if not isinstance(continues, dict) or not continues.get('book'):
            errors.append('continues: needs book (the slug of the earlier book) and, if it came from one, step')
        elif continues['book'] not in prerequisites:
            errors.append(f'continues: "{continues["book"]}" must be in prerequisites')


def other_book_concept(path, data, cid, dep, errors, warnings):
    """A dependency on a concept taught by an earlier book: <slug>:<concept id>."""
    slug, concept = dep.split(':', 1)
    if slug not in (data.get('prerequisites') or []):
        errors.append(f'concept "{cid}": depends on "{dep}", but "{slug}" is not in prerequisites')
        return
    root = library_root(os.path.dirname(path))
    other = library_book(root, slug) if root else None
    if not other:
        warnings.append(f'concept "{cid}": "{slug}" is not in this library, so "{dep}" could not be checked')
    elif concept not in {c.get('id') for c in load_yaml(os.path.join(other, 'book.yaml')).get('concepts') or []}:
        errors.append(f'concept "{cid}": {slug} does not teach "{concept}"')


def cmd_validate(args):
    data, errors, warnings = validate(args.path)
    result = {'ok': not errors, 'errors': errors, 'warnings': warnings}
    if not errors:
        result['book'] = {'title': data['title'], 'chapters': len(data['chapters']),
                          'concepts': len(data['concepts']), 'approved': bool(data['approved_on'])}
        remember(args.path)
        result['selected'] = os.path.abspath(args.path)
    out(result, 0 if not errors else 1)


def chapter(data, n):
    for ch in data['chapters']:
        if ch.get('n') == n:
            return ch
    fail(f'chapter {n} is not in book.yaml')


def summaries(data):
    return {p['n']: p.get('summary', '') for p in data.get('progress') or [] if 'n' in p}


def skeleton(data, ch, lab, review):
    n = ch['n']
    lines = [f'# {n}. {ch["title"]}', '',
             f'> 🗺️ **{lab["In this chapter"]}:** <!-- TODO: 1–2 sentences --> · ⏱️ ~{ch.get("minutes", "?")} min', '']
    if n > 1:
        lines += [f'> 🔥 **{lab["Warm-up"]}:** <!-- TODO: 1–2 questions on earlier chapters, answers hidden -->', '',
                  f'## {lab["Where we left off"]}', '', '<!-- TODO: 2–3 sentences -->', '']
    topic_todo = ('<!-- TODO: why → definition → example → code/procedure with real output '
                  '→ diagram → common mistake -->')
    for topic in ch.get('topics') or ['<!-- TODO: topic -->']:
        lines += [f'## {topic}', '', topic_todo, '']
    lines += [f'## 🏋️ {lab["Practice"]}', '',
              '<!-- TODO: worked example → complete it → on your own → challenge -->', '',
              f'## 🧠 {lab["Quick review"]}', '',
              '<!-- TODO: 3–5 questions, at least one from an earlier chapter -->', '',
              f'## 🤖 {lab["Study with an AI tutor"]}', '', '<!-- TODO: 2 ready-to-copy prompts -->', '',
              f'> ➡️ **{lab["Next"]}:** <!-- TODO -->', '',
              f'## 📌 {lab["Summary"]}', '', '<!-- TODO: table: item | one sentence -->', '',
              f'## 📚 {lab["Sources"]}', '', '<!-- TODO: links with the date checked -->', '']
    if review:
        lines += [f'> 🔁 **{lab["Review today"]}:** ' + ', '.join(str(r) for r in review), '']
    return '\n'.join(lines)


def notes(book_dir, path):
    """A research file for the brief: its text, or a flag saying it still has to be written."""
    rel = os.path.relpath(path, book_dir).replace(os.sep, '/')
    if not os.path.exists(path):
        return {'file': rel, 'missing': True}
    with open(path, encoding='utf-8') as f:
        return {'file': rel, 'notes': f.read()}


def original_book(book_dir, slug):
    """The book a translation comes from: in created-books/ or improved-materials/ of the same library,
    or next to the translation (the old layout)."""
    library = os.path.dirname(os.path.dirname(book_dir))
    for folder in ('created-books', 'improved-materials', os.path.basename(os.path.dirname(book_dir))):
        candidate = os.path.join(library, folder, slug)
        if os.path.isdir(candidate):
            return candidate
    return os.path.join(os.path.dirname(book_dir), slug)


def cmd_brief(args):
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    n = args.n
    ch = chapter(data, n)
    if not data.get('translation_of'):  # a translation follows the original's research
        missing = [p for p in [os.path.join(book_dir, 'research', 'guide.md')]
                   + [research_path(book_dir, k) for k in chapter_numbers(data)] if not os.path.exists(p)]
        if missing:
            names = ', '.join(os.path.relpath(p, book_dir).replace(os.sep, '/') for p in missing)
            fail(f'research first, for every chapter of the book (SOURCES.md §2), even if only some chapters '
                 f'are written now: missing {names}')
    lab = labels(data.get('language', 'en'))
    # spaced review: 1, 3, 7 and 15 chapters back
    review = sorted({n - k for k in (1, 3, 7, 15) if n - k >= 1})
    file = chapter_path(book_dir, n)
    created = False
    if not file:
        file = os.path.join(book_dir, 'chapters', f'{n:02d}-{slugify(ch["title"])}.md')
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'w', encoding='utf-8', newline='\n') as f:
            f.write(skeleton(data, ch, lab, review))
        created = True
    done = summaries(data)
    others = {c['n']: c for c in data['chapters']}
    brief = {**handoff(data),
        'chapter': {k: ch.get(k) for k in ('n', 'title', 'goal', 'topics', 'minutes')},
        'file': os.path.relpath(file, book_dir).replace(os.sep, '/'),
        'skeleton_created': created,
        'language': data.get('language'), 'profiles': data.get('profiles'), 'choices': data.get('choices'),
        'previous': {'n': n - 1, 'title': others[n - 1]['title'], 'summary': done.get(n - 1, '')} if n > 1 else None,
        'next': {'n': n + 1, 'title': others[n + 1]['title']} if n + 1 in others else None,
        'concepts_you_may_use': [c['name'] for c in data['concepts'] if c.get('chapter', n) < n],
        'concepts_to_teach': [c['name'] for c in data['concepts'] if c.get('chapter') == n],
        'warm_up_from': [k for k in (n - 1, n - 2) if k >= 1],
        'review_today': review,
        'sources': [{'title': s['title'], 'url': s['url']} for s in data.get('sources') or []],
    }
    brief['guide'] = notes(book_dir, os.path.join(book_dir, 'research', 'guide.md'))
    brief['research'] = notes(book_dir, research_path(book_dir, n))
    if ch.get('sources_original'):
        brief['original_sections'] = ch['sources_original']
    if data.get('translation_of'):
        original = original_book(book_dir, data['translation_of'])
        source = chapter_path(original, n) or original
        brief['original_chapter'] = os.path.relpath(source, book_dir).replace(os.sep, '/')
        brief['glossary'] = data.get('glossary')
    out(brief)


SKIP_REREAD = re.compile(r'^\s*(!\[|</?(details|summary)\b|\|?\s*:?-{3,})')


def prose(text):
    """The lines a native reader rereads, numbered as in the file: no code blocks, images or HTML tags."""
    lines, fenced = [], False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(('```', '~~~')):
            fenced = not fenced
            continue
        if fenced or not line.strip() or SKIP_REREAD.match(line):
            continue
        lines.append(f'{number}: {line}')
    return lines


def pending_rereads(data):
    """{chapter: code} of the rereads not yet used by `done`; an old list form has no codes."""
    value = data.get('reread')
    return {int(k): str(v) for k, v in value.items()} if isinstance(value, dict) else {}


def cmd_reread(args):
    """Step 5 of the chapter loop, done for real: the chapter's prose comes back to be read as a native
    reader would. A new code comes after the lines and `done` asks for it, so a reread whose output was
    thrown away (`reread >/dev/null; done`) does not count."""
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    chapter(data, args.n)
    file = chapter_path(book_dir, args.n)
    if not file:
        fail(f'chapter {args.n} has no file yet: run "book.py brief {args.n}" first')
    language = data.get('language', 'en')
    style = f'references/style/{language}.md'
    if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), style)):
        style = 'references/style/en.md (the general rules; adapt them to the book language)'
    code = secrets.token_hex(3)
    data['reread'] = {**pending_rereads(data), args.n: code}
    save_yaml(path, data)
    out({'file': os.path.relpath(file, book_dir).replace(os.sep, '/'), 'style': style,
         'do': 'Read every line below as a native reader of the book language, following the style file: '
               'fix (Edit) each sentence that sounds translated, unnatural or unclear; then run '
               f'audit.py {args.n} and book.py done {args.n} --reread <the code after the lines>.',
         'lines': prose(open(file, encoding='utf-8').read()),
         'code': code})


def cmd_done(args):
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    chapter(data, args.n)
    file = chapter_path(book_dir, args.n)
    if not file:
        fail(f'chapter {args.n} has no file yet: run "book.py brief {args.n}" first')
    left = open(file, encoding='utf-8').read().count(TODO)
    if left:
        fail(f'chapter {args.n} still has {left} TODO placeholder(s): finish it and run audit.py {args.n}')
    summary = (args.summary or '').strip()
    if not summary:
        fail('--summary is required (3 to 5 lines: what it taught, terms, examples used)')
    rereads = pending_rereads(data)
    how = (f'run "book.py reread {args.n}", read every line it prints as a native reader, fix what sounds '
           f'translated, then audit.py {args.n} and done with --reread <the code printed after the lines>')
    if args.n not in rereads:
        fail(f'chapter {args.n} was not reread: {how}')
    if args.reread != rereads[args.n]:
        fail(f'chapter {args.n}: missing or wrong reread code. Never throw away the reread output or run '
             f'reread and done in one command: {how}')
    today = datetime.date.today().isoformat()
    del rereads[args.n]
    if rereads:
        data['reread'] = rereads
    else:
        data.pop('reread', None)
    progress = [p for p in data.get('progress') or [] if p.get('n') != args.n]
    progress.append({'n': args.n, 'done': today, 'reread': today, 'summary': summary[:800]})
    data['progress'] = sorted(progress, key=lambda p: p['n'])
    save_yaml(path, data)
    total = len(data['chapters'])
    pending = [c['n'] for c in data['chapters'] if c['n'] not in {p['n'] for p in data['progress']}]
    out({'saved': True, 'progress': f'{total - len(pending)}/{total}',
         'next': f'book.py brief {pending[0]}' if pending else 'fixed parts (references/BOOK.md), then audit.py'})


def handoff(data):
    """The note left for the next conversation, shown first; nothing when there is none."""
    return {'handoff': data['handoff']} if data.get('handoff') else {}


def cmd_handoff(args):
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    items = [i.strip() for i in args.items if i.strip()]
    if items:
        data['handoff'] = items
    else:
        data.pop('handoff', None)
    save_yaml(path, data)
    out({'saved': True, 'handoff': items})


def find_base(arg, library):
    """(folder, root) of the book named by a folder or a slug."""
    if os.path.exists(os.path.join(arg, 'book.yaml')):
        folder = os.path.abspath(arg)
        return folder, library or library_root(folder)
    root = os.path.abspath(library) if library else library_root(os.getcwd())
    if not root:
        selected = find_book(None)[0]
        root = library_root(selected)
    folder = library_book(root, arg) if root else None
    if not folder:
        fail(f'book "{arg}" not found in the library' + (f'; it has: {", ".join(library_slugs(root))}' if root else
                                                           ': pass --library <repository folder>'))
    return folder, root


def cmd_base(args):
    folder, root = find_base(args.book_ref, args.library)
    data = load_yaml(os.path.join(folder, 'book.yaml'))
    note = ''
    if data.get('translation_of') and root and library_book(root, data['translation_of']):
        note = f'{data["slug"]} is a translation: this is its original, {data["translation_of"]}'
        folder = library_book(root, data['translation_of'])
        data = load_yaml(os.path.join(folder, 'book.yaml'))
    done = summaries(data)
    steps = next_steps(data)
    if root:  # books already written from a step, even before book.py link
        for slug in library_slugs(root):
            other = load_yaml(os.path.join(library_book(root, slug), 'book.yaml')).get('continues') or {}
            if other.get('book') == data['slug'] and isinstance(other.get('step'), int) \
                    and 1 <= other['step'] <= len(steps):
                steps[other['step'] - 1].setdefault('book', slug)
    track = data.get('track') or {}
    result = {
        'book': {'title': data['title'], 'slug': data['slug'],
                 'folder': os.path.relpath(folder, root).replace(os.sep, '/') if root else folder,
                 'language': data.get('language')},
        'level': data.get('level'), 'goal': data.get('goal'), 'track': track or None,
        'covers': data.get('covers') or [],
        'concepts': [{'id': c['id'], 'name': c['name'], 'chapter': c.get('chapter')} for c in data['concepts']],
        'chapters': [{'n': c['n'], 'title': c['title'], 'summary': done.get(c['n'], '')} for c in data['chapters']],
        'next_steps': steps,
        'for_the_new_book': {
            'level_start': (data.get('level') or {}).get('end'), 'prerequisites': [data['slug']],
            'track': {'name': track['name'], 'order': track.get('order', 0) + 1} if track.get('name') else None},
    }
    if note:
        result['note'] = note
    out(result)


def cmd_link(args):
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    continues = data.get('continues') or {}
    if not continues.get('book'):
        fail('this book has no "continues" in book.yaml: nothing to link')
    root = library_root(book_dir)
    earlier = library_book(root, continues['book']) if root else None
    if not earlier:
        fail(f'"{continues["book"]}" not found in the library')
    earlier_yaml = os.path.join(earlier, 'book.yaml')
    other = load_yaml(earlier_yaml)
    steps = list(other.get('next_steps') or [])
    step = continues.get('step')
    if isinstance(step, int) and 1 <= step <= len(steps):
        entry = {'title': steps[step - 1]} if isinstance(steps[step - 1], str) else dict(steps[step - 1])
    else:
        entry = {'title': data['title'], 'why': data.get('goal', ''),
                 'topics': [c['title'] for c in data['chapters']][:4]}
        steps.append(entry)
        step = len(steps)
    entry['book'] = data['slug']
    steps[step - 1] = entry
    other['next_steps'] = steps
    save_yaml(earlier_yaml, other)
    out({'linked': continues['book'], 'step': step, 'title': entry['title']})


def cmd_review(args):
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    limit = datetime.date.today() - datetime.timedelta(days=STALE_DAYS)
    stale = [{'title': s['title'], 'url': s['url'], 'checked': str(s.get('checked', ''))}
             for s in data.get('sources') or [] if isinstance(s, dict)
             and (not DATE_RE.match(str(s.get('checked', ''))) or str(s['checked']) < limit.isoformat())]
    audit = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audit.py'),
                            '--book', book_dir], capture_output=True, text=True, encoding='utf-8')
    try:
        report = json.loads(audit.stdout)
    except json.JSONDecodeError:
        report = {'errors': [f'audit.py failed: {audit.stderr.strip()[-300:]}'], 'warnings': []}
    out({'title': data.get('title'), 'edition': str(data.get('edition', '1.0')),
         'reviewed_on': data.get('reviewed_on') or data.get('approved_on'), 'review_by': data.get('review_by'),
         'due': review_due(data), 'reference_version': data.get('reference_version'),
         'stale_sources': stale, 'audit': {'errors': report.get('errors', []), 'warnings': report.get('warnings', [])},
         'next': 'read the reported errors (issues on the library repository), reopen the stale sources, run '
                 'projects.py and the chapters\' commands again, then show the review assessment (modes/REVIEW.md)'})


def cmd_edition(args):
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    current = str(data.get('edition', '1.0'))
    if not EDITION_RE.match(args.edition):
        fail(f'edition "{args.edition}": write it like 1.1, 1.1.1 or 2.0')

    def number(e):  # 1.3 and 1.3.0 are the same edition
        return tuple(int(x) for x in e.split('.')) + (0,) * (3 - e.count('.') - 1)
    if EDITION_RE.match(current) and number(args.edition) <= number(current):
        fail(f'edition {args.edition} must be newer than {current}')
    summary = (args.summary or '').strip()
    if not summary:
        fail('--summary is required (one or two lines: what changed in this edition)')
    if args.review_by and not MONTH_RE.match(args.review_by):
        fail('--review-by: write the month as YYYY-MM')
    today = datetime.date.today().isoformat()
    data['edition'], data['reviewed_on'] = args.edition, today
    if args.review_by:
        data['review_by'] = args.review_by
    data['editions'] = list(data.get('editions') or []) + [{'edition': args.edition, 'date': today,
                                                            'summary': summary[:400]}]
    save_yaml(path, data)
    out({'saved': True, 'edition': args.edition, 'reviewed_on': today, 'review_by': data.get('review_by')})


def cmd_status(args):
    book_dir, path = find_book(args.book)
    data = load_yaml(path)
    lab = labels(data.get('language', 'en'))
    done = sorted(summaries(data))
    pending = [n for n in chapter_numbers(data) if n not in done]
    files = os.listdir(os.path.join(book_dir, 'chapters')) if os.path.isdir(os.path.join(book_dir, 'chapters')) else []
    fixed = {'chapter 0': any(f.startswith('00-') for f in files),
             'mock exam': any(slugify(lab['Final mock exam']) in f for f in files),
             'glossary': any(slugify(lab['Glossary']) in f for f in files)}
    if not data.get('approved_on'):
        step = 'syllabus not approved yet'
    elif not data.get('choices'):
        step = 'ask the choices (images, reading) and save them in book.yaml'
    elif pending:
        step = f'book.py brief {pending[0]}'
    elif not all(fixed.values()):
        step = 'write the fixed parts: ' + ', '.join(k for k, v in fixed.items() if not v)
    else:
        step = 'audit.py (whole book), then build.py'
    if review_due(data):
        step = f'review due since {data["review_by"]}: offer a review (modes/REVIEW.md)'
    due = {'review_due': True} if review_due(data) else {}
    out({**handoff(data), **due, 'title': data.get('title'), 'slug': data.get('slug'), 'language': data.get('language'),
         'approved': bool(data.get('approved_on')), 'chapters_done': f'{len(done)}/{len(chapter_numbers(data))}',
         'pending_chapters': pending, 'fixed_parts': fixed, 'next_step': step})


def main():
    p = argparse.ArgumentParser(description='Validate the book, brief chapters and record progress.')
    sub = p.add_subparsers(dest='cmd', required=True)
    v = sub.add_parser('validate')
    v.add_argument('path')
    b = sub.add_parser('brief')
    b.add_argument('n', type=int)
    w = sub.add_parser('reread')
    w.add_argument('n', type=int)
    d = sub.add_parser('done')
    d.add_argument('n', type=int)
    d.add_argument('--summary')
    d.add_argument('--reread', help='the code printed after the lines of "book.py reread <n>"')
    s = sub.add_parser('status')
    h = sub.add_parser('handoff')
    h.add_argument('items', nargs='*')
    a = sub.add_parser('base')
    a.add_argument('book_ref')
    a.add_argument('--library')
    k = sub.add_parser('link')
    r = sub.add_parser('review')
    e = sub.add_parser('edition')
    e.add_argument('edition')
    e.add_argument('--summary')
    e.add_argument('--review-by')
    for q in (b, w, d, s, h, k, r, e):
        q.add_argument('--book')
    args = p.parse_args()
    {'validate': cmd_validate, 'brief': cmd_brief, 'reread': cmd_reread, 'done': cmd_done, 'status': cmd_status,
     'handoff': cmd_handoff, 'base': cmd_base, 'link': cmd_link,
     'review': cmd_review, 'edition': cmd_edition}[args.cmd](args)


if __name__ == '__main__':
    main()
