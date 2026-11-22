#!/usr/bin/env python3
"""Prepares a report of a problem in the skill itself (not in a book) for its maintainers.

Usage:
  python scripts/report.py --what "<what happened>" --file <script or skill file>
                           [--command "<command>"] [--error "<message>" | --error-file F]
                           [--expected "<what should have happened>"] [--send]

Without --send it only prints the report (title and body, to show the user in full) and the link
of a new issue already filled in at github.com/Joshpcbrrj/syllabook. With --send, given only after
the user says yes, it opens the issue with the GitHub CLI (gh); with no gh, or no login, it says so
and the link is the way to send it.

Privacy: the report carries only what is passed here, the skill version and the system. The home
folder, the user name, e-mail addresses and anything that looks like a token or password are
replaced before anything is printed or sent. Never pass passages of the book or of the user's
materials.
"""
import argparse
import getpass
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL, VERSION, fail, out

REPO = 'Joshpcbrrj/syllabook'
TEMPLATE = 'report-error.yml'
WHERE = 'In the skill or scripts (Na skill ou nos scripts)'
MAX_URL = 8000  # GitHub refuses longer links; browsers and proxies too
MAX_ERROR_LINES = 40

SECRETS = [
    r'\bgh[pousr]_[A-Za-z0-9]{20,}', r'\bgithub_pat_\w{20,}', r'\bsk-[A-Za-z0-9_-]{20,}',
    r'\b(?:secret|ntn)_[A-Za-z0-9]{20,}', r'\bxox[abprs]-[A-Za-z0-9-]{10,}', r'\bAKIA[0-9A-Z]{16}\b',
    r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',  # JWT
]
KEY_VALUE = re.compile(r'(?i)\b(token|password|passwd|pwd|secret|api[_-]?key|authorization)(\s*[=:]\s*)("[^"]*"|\S+)')
EMAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')


def user_names():
    names = {os.environ.get('USERNAME', ''), os.environ.get('USER', '')}
    try:
        names.add(getpass.getuser())
    except Exception:  # no user database in some sandboxes
        pass
    return sorted((n for n in names if len(n) >= 3), key=len, reverse=True)


def scrub(text):
    """The text with no home folder, user name, e-mail, token or password."""
    text = text or ''
    text = text.replace(SKILL, '<skill>').replace(SKILL.replace('\\', '/'), '<skill>')
    home = os.path.expanduser('~')
    if len(home) > 1:
        for form in {home, home.replace('\\', '/')}:
            text = re.sub(re.escape(form), '~', text, flags=re.I)
    for pattern in SECRETS:
        text = re.sub(pattern, '<token>', text)
    text = KEY_VALUE.sub(lambda m: m.group(1) + m.group(2) + '<hidden>', text)
    text = EMAIL.sub('<email>', text)
    for name in user_names():
        text = re.sub(r'(?<![A-Za-z0-9])' + re.escape(name) + r'(?![A-Za-z0-9])', '<user>', text, flags=re.I)
    return text.strip()


def system():
    where = 'claude.ai' if os.path.isdir('/mnt/user-data') else 'local'
    return f'{platform.system()} {platform.release()}, Python {platform.python_version()}, {where}'


def tail(text, lines):
    kept = text.splitlines()[-lines:]
    return '\n'.join(kept)


def description(what, command, error, error_lines):
    parts = [what]
    if command:
        parts.append(f'Command:\n\n```text\n{command}\n```')
    if error:
        parts.append(f'Error (last lines):\n\n```text\n{tail(error, error_lines)}\n```')
    parts.append(f'Skill version: {VERSION}\nSystem: {system()}')
    return '\n\n'.join(parts)


def link(title, location, text, expected):
    fields = {'template': TEMPLATE, 'title': title, 'where': WHERE, 'location': location, 'description': text}
    if expected:
        fields['fix'] = expected
    return f'https://github.com/{REPO}/issues/new?' + urllib.parse.urlencode(fields, quote_via=urllib.parse.quote)


def build(what, location, command='', error='', expected=''):
    """(title, body, url): the body as the issue form would write it; the error shortened to fit the link."""
    what, location, command, error, expected = (scrub(x) for x in (what, location, command, error, expected))
    first = what.splitlines()[0] if what else ''
    title = f'[Error] {location}: {first}'
    if len(title) > 100:
        title = title[:97].rstrip() + '...'
    lines = MAX_ERROR_LINES
    while True:
        text = description(what, command, error, lines)
        url = link(title, location, text, expected)
        if len(url) <= MAX_URL or lines <= 1:
            break
        lines //= 2
    if len(url) > MAX_URL:
        fail('the report is too long for a link: shorten --what and --expected')
    body = (f'### Where is the error? (Onde está o erro?)\n\n{WHERE}\n\n'
            f'### Book and chapter, or file (Livro e capítulo, ou arquivo)\n\n{location}\n\n'
            f'### What is wrong? (O que está errado?)\n\n{text}\n\n'
            f'### What would be correct? (Qual seria o certo?) — optional\n\n{expected or "_No response_"}\n')
    return title, body, url


def send(title, body):
    """Opens the issue with gh; returns (url, None) or (None, reason)."""
    gh = shutil.which('gh')
    if not gh:
        return None, 'GitHub CLI (gh) not found'
    if subprocess.run([gh, 'auth', 'status'], capture_output=True).returncode != 0:
        return None, 'gh is not logged in (gh auth login)'
    done = subprocess.run([gh, 'issue', 'create', '--repo', REPO, '--title', title, '--body-file', '-'],
                          input=body, capture_output=True, text=True, encoding='utf-8')
    if done.returncode != 0:
        return None, scrub(done.stderr.strip().splitlines()[-1] if done.stderr.strip() else 'gh issue create failed')
    return done.stdout.strip().splitlines()[-1], None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--what', required=True, help='what happened, in one or two sentences')
    p.add_argument('--file', required=True, help='the script or skill file with the problem (e.g. audit.py)')
    p.add_argument('--command', default='')
    p.add_argument('--error', default='')
    p.add_argument('--error-file')
    p.add_argument('--expected', default='')
    p.add_argument('--send', action='store_true', help='open the issue now: only after the user said yes')
    args = p.parse_args()
    error = args.error
    if args.error_file:
        if not os.path.exists(args.error_file):
            fail(f'file not found: {args.error_file}')
        error = open(args.error_file, encoding='utf-8', errors='replace').read()
    title, body, url = build(args.what, args.file, args.command, error, args.expected)
    result = {'ok': True, 'sent': False, 'title': title, 'body': body, 'url': url}
    if args.send:
        issue, reason = send(title, body)
        if issue:
            result.update(sent=True, issue=issue)
        else:
            result.update(ok=False, reason=f'{reason}: give the user the link to send it')
    out(result, 0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
