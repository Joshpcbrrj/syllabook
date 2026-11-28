"""book.py: every validation rule, the chapter brief and skeleton, progress and status."""
import importlib
import os
import re
import sys

import pytest
from conftest import SAMPLE, edit, load, read, save


def validate_with(cli, tmp_path, change):
    data = load(os.path.join(SAMPLE, 'book.yaml'))
    change(data)
    path = tmp_path / 'draft.yaml'
    save(path, data)
    return cli('book', 'validate', path)


def test_the_sample_book_is_valid_and_gets_selected(cli, book):
    code, r = cli('book', 'validate', book / 'book.yaml')
    assert code == 0 and r['ok'] and not r['warnings'], r
    assert r['book'] == {'title': 'Python do zero (exemplo de teste)', 'chapters': 2, 'concepts': 2, 'approved': True}
    code, r = cli('book', 'status')  # no --book: uses the selection
    assert code == 0 and r['slug'] == 'python-do-zero-teste'


def test_a_missing_file_is_reported(cli, tmp_path):
    code, r = cli('book', 'validate', tmp_path / 'nope.yaml')
    assert code == 1 and 'file not found' in r['error']


ERRORS = [
    ('missing field', lambda d: d.pop('goal'), 'missing field: goal'),
    ('bad slug', lambda d: d.update(slug='Python Zero'), 'slug:'),
    ('bad origin', lambda d: d.update(origin='copied'), 'origin:'),
    ('no profile', lambda d: d.update(profiles=[]), 'profiles:'),
    ('three profiles', lambda d: d.update(profiles=['stem', 'languages', 'skills']), 'profiles:'),
    ('unknown profile', lambda d: d.update(profiles=['cooking']), 'profiles:'),
    ('level without end', lambda d: d.update(level={'start': 'iniciante'}), 'level:'),
    ('bad image choice', lambda d: d['choices'].update(images='photos'), 'choices.images'),
    ('retired illustrations choice', lambda d: d['choices'].update(images='illustrations'), 'choices.images'),
    ('bad reading choice', lambda d: d['choices'].update(reading='tiny'), 'choices.reading'),
    ('source without url', lambda d: d['sources'][0].pop('url'), 'needs title and url'),
    ('source date', lambda d: d['sources'][0].update(checked='ontem'), 'checked must be'),
    ('chapter gap', lambda d: d['chapters'][1].update(n=3), 'n must go 1, 2, 3'),
    ('chapter without goal', lambda d: d['chapters'][0].pop('goal'), 'chapter 1: missing goal'),
    ('concept id', lambda d: d['concepts'][0].update(id='Lista'), 'id must be lowercase'),
    ('concept twice', lambda d: d['concepts'].append(dict(d['concepts'][0])), 'listed twice'),
    ('concept chapter', lambda d: d['concepts'][0].update(chapter=9), 'chapter 9 does not exist'),
    # {id: x, name: gerenciadores (nvm, SDKMAN, uv)}: in braces, commas split the name into fields
    ('notion_url not a link', lambda d: d.update(notion_url='minha página de livros'), 'notion_url: must be'),
    ('concept split by commas', lambda d: d['concepts'][0].update(name='gerenciadores (nvm', SDKMAN=None),
     'unknown field "SDKMAN"'),
    ('unknown dependency', lambda d: d['concepts'][1].update(depends=['dicionario']), 'unknown concept'),
    ('used before taught', lambda d: (d['concepts'][0].update(chapter=2), d['concepts'][1].update(chapter=1)),
     'taught later'),
    ('improved without original', lambda d: d.update(origin='improved', promise={'goal': 1, 'audience': 1,
                                                                                  'level': 1, 'sequence': 1}),
     'missing original'),
    ('improved without promise', lambda d: d.update(origin='improved', original={'title': 'x'}),
     'promise needs'),
    ('translation without glossary', lambda d: d.update(translation_of='python-do-zero'), 'missing glossary'),
    ('approval date', lambda d: d.update(approved_on='ontem'), 'approved_on:'),
]


@pytest.mark.parametrize('case, change, message', ERRORS, ids=[e[0] for e in ERRORS])
def test_each_validation_error(cli, tmp_path, case, change, message):
    code, r = validate_with(cli, tmp_path, change)
    assert code == 1 and any(message in e for e in r['errors']), r['errors']


WARNINGS = [
    ('no sources', lambda d: d.update(sources=[]), 'sources: empty'),
    ('goal that cannot be checked', lambda d: d['chapters'][0].update(goal='Entender listas'), 'cannot be checked'),
    # an eval syllabus had "entender, resolver e evitar conflitos": the weak verb led a list of verbs
    ('weak verb first in a list', lambda d: d['chapters'][0].update(goal='Entender, resolver e evitar conflitos'),
     'cannot be checked'),
    ('weak verb later in a list', lambda d: d['chapters'][0].update(goal='Criar listas e entender índices'),
     'cannot be checked'),
    ('weak verb in English', lambda d: d['chapters'][0].update(goal='Build a list and understand indexes'),
     'cannot be checked'),
    ('weak verb in Spanish', lambda d: d['chapters'][0].update(goal='Crear listas y conocer los índices'),
     'cannot be checked'),
    ('weak book goal', lambda d: d.update(goal='Entender Python e criar scripts'), 'goal: uses a verb'),
    ('no topics', lambda d: d['chapters'][0].pop('topics'), 'no topics'),
    ('no minutes', lambda d: d['chapters'][0].pop('minutes'), 'minutes missing'),
    ('chapter without concepts', lambda d: d['concepts'].pop(), 'teaches no concept'),
    ('improved without mapping', lambda d: d.update(origin='improved', original={'title': 'x'},
                                                   promise={'goal': 1, 'audience': 1, 'level': 1, 'sequence': 1}),
     'sources_original empty'),
    ('too much new content', lambda d: d.update(origin='improved', original={'title': 'x'}, new_content_pct=35,
                                                promise={'goal': 1, 'audience': 1, 'level': 1, 'sequence': 1}),
     'above the ~20% limit'),
]


@pytest.mark.parametrize('url', ['https://www.notion.so/Livro-0a1b2c3d4e5f60718293a4b5c6d7e8f9',
                                 'https://app.notion.com/p/d7e93f537cfa49d6a160aeff28cccc5b'])
def test_the_notion_copy_link_is_kept(cli, tmp_path, url):
    code, r = validate_with(cli, tmp_path, lambda d: d.update(notion_url=url))
    assert code == 0 and r['ok'], r


@pytest.mark.parametrize('images', ['real', 'svg'])
def test_image_choices_real_images_by_context_or_diagrams_only(cli, tmp_path, images):
    code, r = validate_with(cli, tmp_path, lambda d: d['choices'].update(images=images))
    assert code == 0 and r['ok'], r


@pytest.mark.parametrize('goal', ['Calcular a média de uma lista e explicar o resultado',
                                  'Resolver um conflito de merge e evitar os mais comuns',
                                  'Tocar a batida do samba a 80 bpm, sabendo onde cai o tempo forte',
                                  'Explain what a commit records, then make three'])
def test_checkable_goals_get_no_warning(cli, tmp_path, goal):
    code, r = validate_with(cli, tmp_path, lambda d: d['chapters'][0].update(goal=goal))
    assert code == 0 and not any('cannot be checked' in w for w in r['warnings']), r['warnings']


@pytest.mark.parametrize('case, change, message', WARNINGS, ids=[w[0] for w in WARNINGS])
def test_each_validation_warning(cli, tmp_path, case, change, message):
    code, r = validate_with(cli, tmp_path, change)
    assert code == 0 and any(message in w for w in r['warnings']), r['warnings']


def test_brief_creates_a_skeleton_in_the_book_language(cli, book):
    os.remove(book / 'chapters' / '02-o-laco-for.md')
    code, r = cli('book', 'brief', 2, '--book', book)
    assert code == 0 and r['skeleton_created'] and r['file'] == 'chapters/02-o-laco-for.md'
    assert r['concepts_you_may_use'] == ['lista'] and r['concepts_to_teach'] == ['laço for']
    assert r['previous']['title'] == 'Listas' and r['next'] is None and r['warm_up_from'] == [1]
    text = read(book / r['file'])
    for heading in ('# 2. O laço for', '## De onde paramos', '## O laço for', '## 🏋️ Pratique',
                    '## 🧠 Revisão rápida', '## 📚 Fontes', '🔁 **Revise hoje:** 1'):
        assert heading in text, heading


def test_chapter_one_has_no_warm_up_and_no_where_we_left_off(cli, book):
    os.remove(book / 'chapters' / '01-listas.md')
    code, r = cli('book', 'brief', 1, '--book', book)
    text = read(book / r['file'])
    assert 'De onde paramos' not in text and 'Aquecimento' not in text and r['previous'] is None


def test_brief_never_overwrites_a_chapter(cli, book):
    before = read(book / 'chapters' / '01-listas.md')
    code, r = cli('book', 'brief', 1, '--book', book)
    assert code == 0 and not r['skeleton_created'] and read(book / 'chapters' / '01-listas.md') == before


def test_brief_spaced_review_and_previous_summary(cli, book):
    data = load(book / 'book.yaml')
    data['chapters'] = [{'n': n, 'title': f'Capítulo {n}', 'goal': 'Fazer algo', 'topics': ['t'], 'minutes': 10}
                        for n in range(1, 9)]
    data['concepts'] = [{'id': f'c{n}', 'name': f'c{n}', 'chapter': n, 'depends': []} for n in range(1, 9)]
    data['progress'] = [{'n': 7, 'done': '2026-11-20', 'summary': 'Ensinou c7.'}]
    save(book / 'book.yaml', data)
    for n in range(1, 9):
        (book / 'research' / f'c{n:02d}.md').write_text(f'# Dossiê c{n:02d}\n', encoding='utf-8')
    code, r = cli('book', 'brief', 8, '--book', book)
    assert r['review_today'] == [1, 5, 7] and r['previous']['summary'] == 'Ensinou c7.'


def test_brief_for_an_improved_book_lists_the_original_sections(cli, book):
    data = load(book / 'book.yaml')
    data['chapters'][0]['sources_original'] = ['aula-01', 'aula-02']
    save(book / 'book.yaml', data)
    code, r = cli('book', 'brief', 1, '--book', book)
    assert r['original_sections'] == ['aula-01', 'aula-02']


def test_brief_for_a_translation_points_to_the_original_chapter(cli, book, tmp_path):
    import shutil
    shutil.copytree(book, tmp_path / 'python-do-zero')
    data = load(book / 'book.yaml')
    data.update(translation_of='python-do-zero', glossary=[{'source': 'lista', 'target': 'list'}])
    save(book / 'book.yaml', data)
    code, r = cli('book', 'brief', 1, '--book', book)
    assert r['original_chapter'].endswith('python-do-zero/chapters/01-listas.md') and r['glossary']


def test_brief_for_a_chapter_not_in_the_syllabus(cli, book):
    code, r = cli('book', 'brief', 9, '--book', book)
    assert code == 1 and 'chapter 9 is not in book.yaml' in r['error']


REREAD_CODE = re.compile(r'^>>> reread code: ([0-9a-f]{6}) <<<$', re.M)


@pytest.fixture
def reread(monkeypatch, capsys):
    """`book.py reread` prints plain text, not JSON: returns (exit code, text, the code among the lines)."""
    def run(book, n):
        monkeypatch.setattr(sys, 'argv', ['book.py', 'reread', str(n), '--book', str(book)])
        code = 0
        try:
            importlib.import_module('book').main()
        except SystemExit as e:
            code = e.code or 0
        text = capsys.readouterr().out
        found = REREAD_CODE.findall(text)
        return code, text, found[0] if len(found) == 1 else None
    return run


def done(cli, reread, book, n, summary):
    """The end of the chapter loop: the native reread, then done with the code found among the lines."""
    code, text, word = reread(book, n)
    assert code == 0 and word, text
    return cli('book', 'done', n, '--summary', summary, '--reread', word, '--book', book)


def test_done_records_progress_and_points_to_the_next_step(cli, reread, book):
    code, r = done(cli, reread, book, 1, 'Listas e len.')
    assert code == 0 and r == {'saved': True, 'progress': '1/2', 'next': 'book.py brief 2'}
    code, r = done(cli, reread, book, 1, 'Listas, len e índices.')
    assert [p['summary'] for p in load(book / 'book.yaml')['progress']] == ['Listas, len e índices.']
    code, r = done(cli, reread, book, 2, 'Laço for.')
    assert r['progress'] == '2/2' and 'fixed parts' in r['next']


def prose_lines(text):
    return [line for line in text.splitlines() if re.match(r'^\d+: ', line)]


def test_reread_prints_the_prose_with_line_numbers_and_the_style_file(reread, book):
    edit(book / 'chapters' / '01-listas.md', '## Listas', '## Listas\n\n```python\nnums = [1]\n```')
    code, text, word = reread(book, 1)
    assert code == 0 and 'references/style/pt-BR.md' in text and 'chapters/01-listas.md' in text
    lines = prose_lines(text)
    assert any(line.endswith(': ## Listas') for line in lines), lines
    assert not any('nums = [1]' in line for line in lines), 'code is run, not reread'
    number, line = lines[0].split(': ', 1)
    assert read(book / 'chapters' / '01-listas.md').splitlines()[int(number) - 1] == line
    assert not text.lstrip().startswith('{'), 'plain text: no JSON field to pull the code out of'


def test_the_code_hides_among_the_lines_not_at_the_end(reread, book):
    """Pulling out the code, printing a range of lines or only the tail must miss it most of the time."""
    places = set()
    for _ in range(12):
        code, text, word = reread(book, 1)
        rows = text.strip().splitlines()
        at = next(i for i, row in enumerate(rows) if word in row)
        first = next(i for i, row in enumerate(rows) if re.match(r'^\d+: ', row))
        assert first < at < len(rows) - 1, 'the code sits between two lines of the chapter'
        places.add(at)
    assert len(places) > 1, 'its place changes from one reread to the next'


def test_each_reread_gets_a_new_code(reread, book):
    codes = {reread(book, 1)[2] for _ in range(3)}
    assert len(codes) == 3 and None not in codes


def test_done_refuses_a_chapter_that_was_not_reread(cli, book):
    code, r = cli('book', 'done', 1, '--summary', 'Listas.', '--book', book)
    assert code == 1 and 'book.py reread 1' in r['error']


@pytest.mark.parametrize('given', [None, 'abc123'])
def test_done_refuses_a_reread_without_its_code(cli, reread, book, given):
    """`reread >/dev/null; done` in one command: the reread ran, but nobody read its output."""
    reread(book, 1)
    extra = ['--reread', given] if given else []
    code, r = cli('book', 'done', 1, '--summary', 'Listas.', *extra, '--book', book)
    assert code == 1 and 'code' in r['error']


def test_an_old_code_does_not_work_after_a_new_reread(cli, reread, book):
    old = reread(book, 1)[2]
    reread(book, 1)
    code, r = cli('book', 'done', 1, '--summary', 'Listas.', '--reread', old, '--book', book)
    assert code == 1


def test_done_uses_up_the_reread(cli, reread, book):
    """Done again later (after a fix) needs a new reread; the date of the last one stays in progress."""
    first = reread(book, 1)[2]
    done_code, _ = cli('book', 'done', 1, '--summary', 'Listas.', '--reread', first, '--book', book)
    data = load(book / 'book.yaml')
    assert done_code == 0 and 'reread' not in data
    assert data['progress'][0]['reread'] == data['progress'][0]['done']
    code, r = cli('book', 'done', 1, '--summary', 'Listas de novo.', '--reread', first, '--book', book)
    assert code == 1 and 'reread' in r['error']


@pytest.mark.parametrize('setup, message', [
    (lambda b: os.remove(b / 'chapters' / '01-listas.md'), 'has no file yet'),
    (lambda b: edit(b / 'chapters' / '01-listas.md', '## Listas', '## Listas\n\n<!-- TODO: x -->'), 'TODO'),
])
def test_done_refuses_an_unfinished_chapter(cli, book, setup, message):
    setup(book)
    code, r = cli('book', 'done', 1, '--summary', 'x', '--book', book)
    assert code == 1 and message in r['error']


def test_done_requires_a_summary(cli, book):
    code, r = cli('book', 'done', 1, '--book', book)
    assert code == 1 and '--summary is required' in r['error']


@pytest.mark.parametrize('change, step', [
    (lambda d, b: d.update(approved_on=''), 'syllabus not approved yet'),
    (lambda d, b: d.pop('choices'), 'ask the choices'),
    (lambda d, b: None, 'book.py brief 1'),
    (lambda d, b: (d.update(progress=[{'n': 1, 'summary': 'a'}, {'n': 2, 'summary': 'b'}]),
                   os.remove(b / 'chapters' / 'glossario.md')), 'write the fixed parts: glossary'),
    (lambda d, b: d.update(progress=[{'n': 1, 'summary': 'a'}, {'n': 2, 'summary': 'b'}]), 'audit.py'),
])
def test_status_next_step(cli, book, change, step):
    data = load(book / 'book.yaml')
    change(data, book)
    save(book / 'book.yaml', data)
    code, r = cli('book', 'status', '--book', book)
    assert step in r['next_step'], r


def test_brief_includes_the_chapters_research_dossier(cli, book):
    code, r = cli('book', 'brief', 1, '--book', book)
    assert r['research']['file'] == 'research/c01.md' and 'índice é 0' in r['research']['notes']


@pytest.mark.parametrize('chapter', [1, 2])
def test_brief_refuses_until_every_dossier_of_the_book_exists(cli, book, chapter):
    """The dossiers are the judgment of the whole book, made before any chapter (SOURCES.md §2): a session
    once wrote only the dossier of chapter 1 and went on writing."""
    os.remove(book / 'research' / 'c02.md')
    code, r = cli('book', 'brief', chapter, '--book', book)
    assert code == 1 and 'research/c02.md' in r['error'] and 'every chapter' in r['error']


def test_brief_includes_the_topic_guide(cli, book):
    code, r = cli('book', 'brief', 2, '--book', book)
    assert r['guide']['file'] == 'research/guide.md' and 'saída esperada' in r['guide']['notes']


def test_brief_refuses_without_the_topic_guide(cli, book):
    os.remove(book / 'research' / 'guide.md')
    code, r = cli('book', 'brief', 2, '--book', book)
    assert code == 1 and 'research/guide.md' in r['error']


def test_a_translation_needs_no_research_of_its_own(cli, book, tmp_path):
    import shutil
    shutil.copytree(book, tmp_path / 'python-do-zero')
    shutil.rmtree(book / 'research')
    data = load(book / 'book.yaml')
    data.update(translation_of='python-do-zero', glossary=[{'source': 'lista', 'target': 'list'}])
    save(book / 'book.yaml', data)
    code, r = cli('book', 'brief', 1, '--book', book)
    assert code == 0 and r['original_chapter'], r


@pytest.mark.parametrize('handoff', ['capturas', [''], [1], {'a': 'b'}], ids=['text', 'empty', 'number', 'map'])
def test_handoff_must_be_a_list_of_sentences(cli, tmp_path, handoff):
    code, r = validate_with(cli, tmp_path, lambda d: d.update(handoff=handoff))
    assert code == 1 and any('handoff:' in e for e in r['errors']), r['errors']


def test_handoff_is_saved_and_shown_first_when_resuming(cli, book):
    items = ['Captura do VS Code pedida para o cap. 1', 'Próximo: cap. 2 em conversa nova']
    code, r = cli('book', 'handoff', *items, '--book', book)
    assert code == 0 and r == {'saved': True, 'handoff': items}
    assert load(book / 'book.yaml')['handoff'] == items
    code, r = cli('book', 'validate', book / 'book.yaml')
    assert code == 0, r
    code, r = cli('book', 'status', '--book', book)
    assert r['handoff'] == items and list(r)[0] == 'handoff'
    code, r = cli('book', 'brief', 2, '--book', book)
    assert r['handoff'] == items


def test_handoff_without_items_clears_it(cli, book):
    cli('book', 'handoff', 'algo pendente', '--book', book)
    code, r = cli('book', 'handoff', '--book', book)
    assert code == 0 and r == {'saved': True, 'handoff': []}
    assert 'handoff' not in load(book / 'book.yaml')
    code, r = cli('book', 'status', '--book', book)
    assert 'handoff' not in r
    code, r = cli('book', 'brief', 1, '--book', book)
    assert 'handoff' not in r
