"""report.py: the problem report carries no personal data, fits a link and is sent only with --send."""
import os
import re
import subprocess
import urllib.parse

import common
import report
from conftest import ROOT, SKILL, read


def fields(url):
    return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).items()}


def test_scrub_removes_home_user_email_and_secrets(monkeypatch):
    home = os.path.expanduser('~')
    monkeypatch.setenv('USERNAME', 'mariasilva')
    text = (f'{home}{os.sep}livros{os.sep}git\\book.yaml not found; C:/Users/MariaSilva/x.md\n'
            'author maria.silva@exemplo.com.br token=abc123 password: "s3 cr3t"\n'
            'ghp_' + 'a' * 36 + ' github_pat_' + 'b' * 30 + ' ntn_' + 'c' * 30 + ' sk-' + 'd' * 30)
    clean = report.scrub(text)
    for leaked in (home, 'mariasilva', 'MariaSilva', 'maria.silva@', 'abc123', 's3 cr3t',
                   'ghp_', 'github_pat_', 'ntn_', 'sk-d'):
        assert leaked not in clean, leaked
    assert '~' in clean and '<user>' in clean and '<email>' in clean and 'token=<hidden>' in clean


def test_scrub_shortens_the_skill_folder():
    assert report.scrub(os.path.join(SKILL, 'scripts', 'audit.py')) == os.path.join('<skill>', 'scripts', 'audit.py')


def test_report_prints_title_body_and_a_prefilled_link_without_sending(cli, monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: calls.append(a))
    code, res = cli('report', '--what', 'audit.py flags a valid link as broken', '--file', 'audit.py',
                    '--command', 'python scripts/audit.py 3', '--error', 'Traceback\nKeyError: x',
                    '--expected', 'no warning')
    assert code == 0 and res['ok'] and res['sent'] is False and calls == []
    assert res['title'] == '[Error] audit.py: audit.py flags a valid link as broken'
    f = fields(res['url'])
    assert res['url'].startswith('https://github.com/Joshpcbrrj/syllabook/issues/new?')
    assert f['template'] == 'report-error.yml' and f['location'] == 'audit.py' and f['fix'] == 'no warning'
    assert 'KeyError: x' in f['description'] and f'Skill version: {common.VERSION}' in f['description']
    assert f['description'] in res['body'] and 'no warning' in res['body']


def test_link_uses_the_ids_and_the_option_of_the_issue_form():
    form = read(os.path.join(ROOT, '.github', 'ISSUE_TEMPLATE', report.TEMPLATE))
    for field in ('where', 'location', 'description', 'fix'):
        assert f'id: {field}\n' in form
    assert f'- {report.WHERE}\n' in form


def test_a_long_error_is_cut_to_its_last_lines_so_the_link_fits():
    error = '\n'.join(f'line {i}: ' + 'x' * 150 for i in range(500))
    title, body, url = report.build('crash', 'build.py', error=error)
    assert len(url) <= report.MAX_URL
    assert 'line 499' in body and 'line 0:' not in body


def test_a_long_title_is_cut():
    title, _, _ = report.build('word ' * 60, 'book.py')
    assert len(title) <= 100 and title.endswith('...')


def test_error_file_is_read_and_scrubbed(cli, tmp_path):
    log = tmp_path / 'err.txt'
    log.write_text(f'failed at {os.path.expanduser("~")}{os.sep}x\n', encoding='utf-8')
    code, res = cli('report', '--what', 'fails', '--file', 'build.py', '--error-file', log)
    assert code == 0 and os.path.expanduser('~') not in res['body'] and 'failed at ~' in res['body']
    code, res = cli('report', '--what', 'fails', '--file', 'build.py', '--error-file', tmp_path / 'none.txt')
    assert code == 1 and 'file not found' in res['error']


def test_send_without_gh_gives_the_link_instead(cli, monkeypatch):
    monkeypatch.setattr(report.shutil, 'which', lambda name: None)
    code, res = cli('report', '--what', 'fails', '--file', 'build.py', '--send')
    assert code == 1 and not res['sent'] and 'gh' in res['reason'] and res['url']


def test_send_opens_the_issue_with_gh(cli, monkeypatch):
    seen = []

    class Done:
        def __init__(self, code=0, stdout='', stderr=''):
            self.returncode, self.stdout, self.stderr = code, stdout, stderr

    def run(cmd, **kw):
        seen.append((cmd, kw.get('input')))
        return Done(stdout='https://github.com/Joshpcbrrj/syllabook/issues/99\n')
    monkeypatch.setattr(report.shutil, 'which', lambda name: 'gh')
    monkeypatch.setattr(report.subprocess, 'run', run)
    code, res = cli('report', '--what', 'fails', '--file', 'build.py', '--send')
    assert code == 0 and res['sent'] and res['issue'].endswith('/issues/99')
    create = seen[-1][0]
    assert create[:3] == ['gh', 'issue', 'create'] and report.REPO in create
    assert seen[-1][1] == res['body']


def test_send_reports_a_gh_failure(cli, monkeypatch):
    class Done:
        def __init__(self, code, stderr=''):
            self.returncode, self.stdout, self.stderr = code, '', stderr
    answers = iter([Done(0), Done(1, 'HTTP 403: Resource not accessible')])
    monkeypatch.setattr(report.shutil, 'which', lambda name: 'gh')
    monkeypatch.setattr(report.subprocess, 'run', lambda *a, **k: next(answers))
    code, res = cli('report', '--what', 'fails', '--file', 'build.py', '--send')
    assert code == 1 and 'HTTP 403' in res['reason']
    monkeypatch.setattr(report.subprocess, 'run', lambda *a, **k: Done(1))
    code, res = cli('report', '--what', 'fails', '--file', 'build.py', '--send')
    assert code == 1 and 'not logged in' in res['reason']


def test_version_follows_the_changelog():
    """At a release, VERSION must become the released number; with unreleased changes, the next one plus -dev."""
    text = read(os.path.join(ROOT, 'CHANGELOG.md'))
    released = re.findall(r'^## \[(\d+\.\d+\.\d+)\]', text, re.M)
    unreleased = re.search(r'^## \[Unreleased\]\n(.*?)(?=^## \[)', text, re.M | re.S)
    pending = bool(unreleased and re.search(r'^- ', unreleased.group(1), re.M))
    latest = tuple(map(int, released[0].split('.')))
    if pending:
        assert common.VERSION.endswith('-dev'), 'CHANGELOG has unreleased changes: VERSION should end in -dev'
        assert tuple(map(int, common.VERSION[:-4].split('.'))) > latest
    else:
        assert common.VERSION == released[0]
