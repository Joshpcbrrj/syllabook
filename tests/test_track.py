"""Books in a track: rich next steps, a follow-up book built on an earlier one, and the link back."""
import shutil

import pytest
from conftest import SAMPLE, load, read, save

FIRST = 'python-do-zero-teste'
STEPS = [{'title': 'Funções em Python', 'why': 'Para não repetir o mesmo cálculo em vários lugares.',
          'topics': ['def e return', 'parâmetros', 'escopo']},
         'Arquivos em Python']


@pytest.fixture
def track(library):
    """The sample book with progress and rich next steps, and a follow-up book that continues it."""
    first = library / 'created-books' / FIRST
    data = load(first / 'book.yaml')
    data.update(next_steps=STEPS, track={'name': 'python', 'order': 1},
                progress=[{'n': 1, 'done': '2026-11-20', 'summary': 'Listas, len e índices.'},
                          {'n': 2, 'done': '2026-11-20', 'summary': 'Laço for e média.'}])
    save(first / 'book.yaml', data)
    second = library / 'created-books' / 'funcoes-em-python'
    shutil.copytree(SAMPLE, second)
    data = load(second / 'book.yaml')
    data.update(slug='funcoes-em-python', title='Funções em Python', prerequisites=[FIRST],
                track={'name': 'python', 'order': 2}, continues={'book': FIRST, 'step': 1},
                level={'start': 'iniciante', 'end': 'intermediário'}, next_steps=[], progress=[])
    data['concepts'] = [{'id': 'funcao', 'name': 'função', 'chapter': 1, 'depends': [f'{FIRST}:lista']},
                        {'id': 'retorno', 'name': 'retorno', 'chapter': 2, 'depends': ['funcao', f'{FIRST}:laco-for']}]
    save(second / 'book.yaml', data)
    return library, first, second


def validate(cli, path, change=None):
    if change:
        data = load(path / 'book.yaml')
        change(data)
        save(path / 'book.yaml', data)
    return cli('book', 'validate', path / 'book.yaml')


def test_rich_next_steps_and_a_track_are_valid(cli, track):
    _, first, second = track
    for book in (first, second):
        code, r = validate(cli, book)
        assert code == 0 and not r['errors'], r


ERRORS = [
    ('step without title', lambda d: d.update(next_steps=[{'why': 'x'}]), 'next_steps[1]: needs a title'),
    ('topics not a list', lambda d: d.update(next_steps=[{'title': 'x', 'topics': 'a, b'}]), 'topics must be a list'),
    ('prerequisites not a list', lambda d: d.update(prerequisites='docker'), 'prerequisites: must be a list'),
    ('track without order', lambda d: d.update(track={'name': 'python'}), 'track: needs name and order'),
    ('continues an unlisted book', lambda d: d.update(continues={'book': 'outro-livro', 'step': 1}),
     'continues: "outro-livro" must be in prerequisites'),
    ('depends on a book not in prerequisites', lambda d: d['concepts'][0].update(depends=['outro-livro:lista']),
     '"outro-livro" is not in prerequisites'),
    ('depends on a concept the earlier book does not teach', lambda d: d['concepts'][0].update(
        depends=[f'{FIRST}:dicionario']), f'{FIRST} does not teach "dicionario"'),
]


@pytest.mark.parametrize('case, change, message', ERRORS, ids=[e[0] for e in ERRORS])
def test_each_track_error(cli, track, case, change, message):
    _, _, second = track
    code, r = validate(cli, second, change)
    assert code == 1 and any(message in e for e in r['errors']), r['errors']


def test_a_concept_from_a_book_outside_the_library_is_only_a_warning(cli, track):
    _, _, second = track
    code, r = validate(cli, second, lambda d: (d.update(prerequisites=[FIRST, 'docker-do-zero']),
                                                d['concepts'][0].update(depends=['docker-do-zero:container'])))
    assert code == 0 and any('docker-do-zero' in w and 'not in this library' in w for w in r['warnings']), r


def test_base_summarizes_a_book_for_the_next_one(cli, track):
    library, _, _ = track
    code, r = cli('book', 'base', FIRST, '--library', library)
    assert code == 0, r
    assert r['book'] == {'title': 'Python do zero (exemplo de teste)', 'slug': FIRST,
                         'folder': f'created-books/{FIRST}', 'language': 'pt-BR'}
    assert r['level'] == {'start': 'iniciante', 'end': 'iniciante'} and r['covers'] == ['lista', 'laco-for']
    assert r['concepts'] == [{'id': 'lista', 'name': 'lista', 'chapter': 1},
                             {'id': 'laco-for', 'name': 'laço for', 'chapter': 2}]
    assert r['chapters'][1] == {'n': 2, 'title': 'O laço for', 'summary': 'Laço for e média.'}
    assert r['next_steps'][0] == {'step': 1, **STEPS[0], 'book': 'funcoes-em-python'}
    assert r['next_steps'][1] == {'step': 2, 'title': 'Arquivos em Python', 'why': '', 'topics': []}
    assert r['for_the_new_book'] == {'level_start': 'iniciante', 'prerequisites': [FIRST],
                                     'track': {'name': 'python', 'order': 2}}


def test_base_takes_a_folder_too(cli, track):
    library, first, _ = track
    code, r = cli('book', 'base', first)
    assert code == 0 and r['book']['slug'] == FIRST


def test_base_of_a_translation_uses_the_original(cli, track):
    library, first, _ = track
    folder = library / 'translated-books' / f'{FIRST}-en'
    shutil.copytree(first, folder)
    data = load(folder / 'book.yaml')
    data.update(slug=f'{FIRST}-en', language='en', translation_of=FIRST, glossary=[{'source': 'a', 'target': 'b'}])
    save(folder / 'book.yaml', data)
    code, r = cli('book', 'base', f'{FIRST}-en', '--library', library)
    assert code == 0 and r['book']['slug'] == FIRST and 'translation' in r['note']


def test_base_of_a_book_not_in_the_library(cli, track):
    library, _, _ = track
    code, r = cli('book', 'base', 'nao-existe', '--library', library)
    assert code == 1 and 'not found' in r['error'] and FIRST in r['error']  # lists what there is


def test_link_marks_the_step_the_new_book_continues(cli, track):
    _, first, second = track
    code, r = cli('book', 'link', '--book', second)
    assert code == 0 and r == {'linked': FIRST, 'step': 1, 'title': 'Funções em Python'}
    assert load(first / 'book.yaml')['next_steps'][0]['book'] == 'funcoes-em-python'
    assert load(first / 'book.yaml')['next_steps'][1] == 'Arquivos em Python'


def test_link_adds_a_step_when_the_new_book_came_from_the_users_own_idea(cli, track):
    _, first, second = track
    data = load(second / 'book.yaml')
    data['continues'] = {'book': FIRST}
    save(second / 'book.yaml', data)
    code, r = cli('book', 'link', '--book', second)
    steps = load(first / 'book.yaml')['next_steps']
    assert code == 0 and r['step'] == 3 and steps[2]['book'] == 'funcoes-em-python'
    assert steps[2]['title'] == 'Funções em Python' and steps[2]['why']


def test_link_needs_continues(cli, book):
    code, r = cli('book', 'link', '--book', book)
    assert code == 1 and 'continues' in r['error']


def test_build_writes_the_next_steps_at_the_end_of_the_last_chapter(cli, track, tmp_path):
    _, first, second = track
    cli('book', 'link', '--book', second)
    code, r = cli('build', '--book', first, '--out', tmp_path / 'd', '--no-epub', '--no-zip')
    assert code == 0, r
    text = read(first / 'chapters' / '02-o-laco-for.md')
    block = text.split('<!-- next-steps:start -->')[1].split('<!-- next-steps:end -->')[0]
    assert '## 🧭 Próximos caminhos' in block
    assert '[Funções em Python](../../funcoes-em-python/README.md)' in block
    assert 'Para não repetir o mesmo cálculo' in block and 'def e return · parâmetros · escopo' in block
    assert '- **Arquivos em Python**' in block
    assert text.index('<!-- next-steps:end -->') < text.index('<!-- nav:start -->')
    cli('build', '--book', first, '--out', tmp_path / 'd', '--no-epub', '--no-zip')
    assert read(first / 'chapters' / '02-o-laco-for.md').count('<!-- next-steps:start -->') == 1


def test_build_links_a_next_book_in_another_collection(cli, track, tmp_path):
    library, first, second = track
    moved = library / 'improved-materials' / 'funcoes-em-python'
    shutil.move(str(second), str(moved))
    cli('book', 'link', '--book', moved)
    cli('build', '--book', first, '--out', tmp_path / 'd', '--no-epub', '--no-zip')
    assert '(../../../improved-materials/funcoes-em-python/README.md)' in read(first / 'chapters' / '02-o-laco-for.md')
