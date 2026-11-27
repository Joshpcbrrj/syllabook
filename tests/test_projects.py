"""projects.py: assembling projects from code blocks, evolving them, running and checking them."""
import os
import sys

import pytest
from conftest import edit, read

PY = sys.executable.replace('\\', '/')


def add(book, chapter_file, text):
    """Appends text before the Sources section of a chapter."""
    edit(book / 'chapters' / chapter_file, '## 📚 Fontes', text + '\n\n## 📚 Fontes')


def project_block(name, run=None, expect=None):
    marker = f'<!-- project: {name}' + (f' | run: "{PY}" main.py' if run else '') + \
             (f' | expect: {expect}' if expect else '') + ' -->'
    return (f'{marker}\n\n**main.py**\n\n```python\nfrom util import dobro\n# mostra o dobro de 21\n'
            f'print(dobro(21))\n```\n\n**util.py**\n\n```python\ndef dobro(n):\n    return n * 2\n```')


def test_a_project_is_assembled_and_runs(cli, book):
    add(book, '01-listas.md', project_block('calc', run=True, expect='42'))
    code, r = cli('projects', '--book', book)
    assert code == 0 and r['ok'], r
    project = r['projects'][0]
    assert project['name'] == 'calc' and project['status'] == 'ok' and project['files'] == ['main.py', 'util.py']
    assert '42' in project['output']
    assert read(book / 'projects' / 'calc' / 'util.py') == 'def dobro(n):\n    return n * 2\n'


def test_one_chapter_of_a_running_project_uses_the_files_of_the_earlier_chapters(cli, book):
    # chapter 1 writes main.py and util.py; chapter 2 changes only util.py: the project must still run
    add(book, '01-listas.md', project_block('calc', run=True, expect='42'))
    add(book, '02-o-laco-for.md', f'<!-- project: calc | run: "{PY}" main.py | expect: 63 -->\n\n**util.py**\n\n'
                                  '```python\ndef dobro(n):\n    # agora é o triplo\n    return n * 3\n```')
    code, r = cli('projects', '--book', book, '--chapter', 2)
    assert code == 0 and r['ok'], r
    assert r['projects'][0]['files'] == ['main.py', 'util.py'] and '63' in r['projects'][0]['output']


def test_one_chapter_runs_only_the_projects_it_touches(cli, book):
    add(book, '01-listas.md', project_block('calc', run=True, expect='42'))
    code, r = cli('projects', '--book', book, '--chapter', 2)
    assert code == 0 and r['projects'] == []


@pytest.mark.parametrize('name', ['../chapters', '..', 'a/b', 'a\\b'])
def test_a_project_name_that_is_a_path_never_deletes_the_book(cli, book, name):
    add(book, '01-listas.md', project_block(name))
    before = sorted(os.listdir(book / 'chapters'))
    code, r = cli('projects', '--book', book)
    assert code == 1 and any('project name' in e for e in r['errors'])
    assert sorted(os.listdir(book / 'chapters')) == before and not r['projects']


def test_a_later_chapter_evolves_the_same_project(cli, book):
    add(book, '01-listas.md', project_block('calc', run=True, expect='63'))
    add(book, '02-o-laco-for.md', '<!-- project: calc -->\n\n**util.py**\n\n```python\ndef dobro(n):\n'
                                  '    # agora é o triplo: o livro evoluiu o projeto\n    return n * 3\n```')
    code, r = cli('projects', '--book', book)
    assert code == 0 and r['projects'][0]['chapters'] == [1, 2] and '63' in r['projects'][0]['output']


@pytest.mark.parametrize('run, expect, message', [
    (True, '99', 'does not contain "99"'),
])
def test_a_wrong_output_fails(cli, book, run, expect, message):
    add(book, '01-listas.md', project_block('calc', run=run, expect=expect))
    code, r = cli('projects', '--book', book)
    assert code == 1 and not r['ok'] and message in r['projects'][0]['output']


def test_a_crashing_project_fails_with_its_exit_code(cli, book):
    add(book, '01-listas.md', f'<!-- project: quebra | run: "{PY}" main.py -->\n\n**main.py**\n\n'
                              '```python\n# erro de propósito\nraise SystemExit(3)\n```')
    code, r = cli('projects', '--book', book)
    assert code == 1 and 'exit code 3' in r['projects'][0]['output']


def test_a_project_that_hangs_times_out(cli, book):
    add(book, '01-listas.md', f'<!-- project: lento | run: "{PY}" main.py -->\n\n**main.py**\n\n'
                              '```python\n# espera mais que o limite\nimport time\ntime.sleep(5)\n```')
    code, r = cli('projects', '--book', book, '--timeout', 1)
    assert code == 1 and 'timed out' in r['projects'][0]['output']


def test_a_server_passes_once_its_output_shows_the_expected_text(cli, book):
    # a server never ends by itself: it is stopped when the output shows "expect", well before the timeout
    add(book, '01-listas.md', f'<!-- project: servidor | run: "{PY}" -u main.py | expect: Servidor pronto -->\n\n'
                              '**main.py**\n\n```python\n# sobe e fica no ar\nimport time\nprint("Servidor pronto")\n'
                              'time.sleep(60)\n```')
    code, r = cli('projects', '--book', book, '--timeout', 20)
    assert code == 0 and r['projects'][0]['status'] == 'ok', r
    assert 'Servidor pronto' in r['projects'][0]['output']


def test_a_server_that_never_shows_the_expected_text_times_out(cli, book):
    add(book, '01-listas.md', f'<!-- project: mudo | run: "{PY}" -u main.py | expect: pronto -->\n\n'
                              '**main.py**\n\n```python\n# nunca avisa\nimport time\nprint("subindo")\n'
                              'time.sleep(60)\n```')
    code, r = cli('projects', '--book', book, '--timeout', 2)
    assert code == 1 and 'timed out' in r['projects'][0]['output'] and 'subindo' in r['projects'][0]['output']


def test_files_without_an_extension_and_dotfiles_belong_to_the_project(cli, book):
    add(book, '01-listas.md', '<!-- project: api -->\n\n**Dockerfile**\n\n```dockerfile\nFROM python:3.14-slim\n```\n\n'
                              '**.dockerignore**\n\n```text\n.venv\n```\n\n**app/Makefile**\n\n```make\nall:\n```\n\n'
                              '**Resultado**\n\n```text\nnão é um arquivo\n```')
    code, r = cli('projects', '--book', book)
    assert code == 0 and r['projects'][0]['files'] == ['.dockerignore', 'Dockerfile', 'app/Makefile'], r


def test_blocks_before_the_marker_of_a_chapter_are_loose_examples(cli, book):
    add(book, '01-listas.md', '**~/.bashrc**\n\n```bash\n# exemplo solto\nalias ll="ls -l"\n```\n\n'
                              + project_block('calc', run=True, expect='42'))
    code, r = cli('projects', '--book', book)
    assert code == 0 and [p['name'] for p in r['projects']] == ['calc'], r


def test_without_a_marker_the_project_is_named_after_the_chapter_and_not_run(cli, book):
    add(book, '02-o-laco-for.md', '**media.py**\n\n```python\n# calcula a média\nprint(7.33)\n```')
    code, r = cli('projects', '--book', book)
    assert code == 0 and r['projects'][0]['name'] == '02-o-laco-for'
    assert r['projects'][0]['status'].startswith('not run')


def test_no_run_and_chapter_filter(cli, book):
    add(book, '01-listas.md', project_block('calc', run=True))
    add(book, '02-o-laco-for.md', project_block('outro', run=True))
    code, r = cli('projects', '--book', book, '--chapter', 2, '--no-run')
    assert [p['name'] for p in r['projects']] == ['outro'] and 'no-run' in r['projects'][0]['status']


def test_blocks_inside_quotes_and_answers_count(cli, book):
    add(book, '01-listas.md', '> <!-- project: citado -->\n>\n> **a.py**\n>\n> ```python\n> # dentro de citação\n'
                              '> print(1)\n> ```')
    code, r = cli('projects', '--book', book)
    assert r['projects'][0]['name'] == 'citado' and r['projects'][0]['files'] == ['a.py']


@pytest.mark.parametrize('path', ['../fora.py', '/etc/passwd.py', 'C:/x.py'])
def test_a_path_that_leaves_the_project_folder_is_refused(cli, book, path):
    add(book, '01-listas.md', f'<!-- project: mau -->\n\n**{path}**\n\n```python\n# fora\nprint(1)\n```')
    code, r = cli('projects', '--book', book)
    assert code == 1 and any('leaves the project folder' in e for e in r['errors'])
    assert not os.path.exists(book / 'fora.py')


def test_a_book_without_projects(cli, book):
    code, r = cli('projects', '--book', book)
    assert code == 0 and r == {'projects': [], 'errors': [], 'ok': True}


def test_a_chapter_without_a_file(cli, book):
    code, r = cli('projects', '--book', book, '--chapter', 9)
    assert code == 1 and 'no file yet' in r['error']


def test_the_project_folder_follows_the_chapters(cli, book):
    add(book, '01-listas.md', project_block('calc'))
    cli('projects', '--book', book)
    edit(book / 'chapters' / '01-listas.md', 'return n * 2', 'return n * 3')
    code, r = cli('projects', '--book', book)
    assert code == 0 and read(book / 'projects' / 'calc' / 'util.py') == 'def dobro(n):\n    return n * 3\n'


@pytest.mark.parametrize('file, content', [('util.py', 'def dobro(n):\n    return n + n\n'),
                                           ('sobra.txt', 'não está no livro\n')])
def test_a_file_changed_by_hand_is_never_lost(cli, book, file, content):
    add(book, '01-listas.md', project_block('calc'))
    cli('projects', '--book', book)
    (book / 'projects' / 'calc' / file).write_text(content, encoding='utf-8')
    code, r = cli('projects', '--book', book)
    assert code == 1 and any(file in e and 'by hand' in e for e in r['errors']), r
    assert read(book / 'projects' / 'calc' / file) == content
    code, r = cli('projects', '--book', book, '--discard')
    assert code == 0 and read(book / 'projects' / 'calc' / 'util.py') == 'def dobro(n):\n    return n * 2\n'
    assert not (book / 'projects' / 'calc' / 'sobra.txt').exists()


def test_a_checkout_with_windows_line_endings_is_not_a_change(cli, book):
    add(book, '01-listas.md', project_block('calc'))
    cli('projects', '--book', book)
    util = book / 'projects' / 'calc' / 'util.py'
    util.write_bytes(util.read_bytes().replace(b'\n', b'\r\n'))  # git with core.autocrlf on Windows
    code, r = cli('projects', '--book', book)
    assert code == 0, r


def test_what_the_run_creates_is_cleaned_without_asking(cli, book):
    add(book, '01-listas.md', project_block('calc', run=True, expect='42'))
    cli('projects', '--book', book)
    assert (book / 'projects' / 'calc' / '__pycache__').is_dir()  # written by Python on the run
    code, r = cli('projects', '--book', book)
    assert code == 0, r


def test_a_book_assembled_before_the_record_keeps_files_that_differ(cli, book):
    add(book, '01-listas.md', project_block('calc'))
    folder = book / 'projects' / 'calc'
    folder.mkdir(parents=True)
    (folder / 'main.py').write_text('from util import dobro\n# mostra o dobro de 21\nprint(dobro(21))\n')
    (folder / 'util.py').write_text('def dobro(n):\n    return n + n\n')
    code, r = cli('projects', '--book', book)
    assert code == 1 and any('util.py' in e and 'main.py' not in e for e in r['errors']), r
