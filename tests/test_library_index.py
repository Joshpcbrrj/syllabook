"""The library's index by track, and the audit that keeps the original of an improved book out of it."""
import shutil

import pytest
from conftest import SAMPLE, edit, load, read, save

FIRST = 'python-do-zero-teste'


def add_book(library, folder, slug, title, **fields):
    path = library / folder / slug
    shutil.copytree(SAMPLE, path)
    data = load(path / 'book.yaml')
    data.update(slug=slug, title=title, **fields)
    save(path / 'book.yaml', data)
    return path


@pytest.fixture
def tracked(library):
    first = library / 'created-books' / FIRST
    data = load(first / 'book.yaml')
    data['track'] = {'name': 'python', 'order': 1}
    save(first / 'book.yaml', data)
    add_book(library, 'improved-materials', 'funcoes-em-python', 'Funções em Python',
             origin='improved', track={'name': 'python', 'order': 2})
    add_book(library, 'created-books', 'violao-basico', 'Violão básico')
    add_book(library, 'translated-books', f'{FIRST}-en', 'Python from scratch', language='en',
             translation_of=FIRST, track={'name': 'python', 'order': 1})
    return library


def test_lists_write_the_tracks_on_the_front_page(cli, tracked):
    code, r = cli('build', 'lists', '--library', tracked)
    assert code == 0 and 'README.pt-BR.md' in r['updated'] and 'README.md' in r['updated']
    front = read(tracked / 'README.pt-BR.md')
    block = front.split('<!-- tracks:start -->')[1].split('<!-- tracks:end -->')[0]
    assert '## 🧭 Trilhas' in block
    assert (f'- **Python:** [Python do zero (exemplo de teste)](created-books/{FIRST}/) → '
            '[Funções em Python](improved-materials/funcoes-em-python/)') in block
    assert '- **Outros livros:** [Violão básico](created-books/violao-basico/)' in block
    assert 'Python from scratch' not in block  # a translation is listed with its own collection, not in the track
    assert '## 🧭 Tracks' in read(tracked / 'README.md')


def test_a_track_name_from_library_yaml(cli, tracked):
    settings = load(tracked / 'library.yaml')
    settings['tracks'] = {'python': 'Programação em Python'}
    save(tracked / 'library.yaml', settings)
    cli('build', 'lists', '--library', tracked)
    assert '- **Programação em Python:**' in read(tracked / 'README.pt-BR.md')


def test_no_tracks_no_section(cli, library):
    before = read(library / 'README.pt-BR.md')
    cli('build', 'lists', '--library', library)
    assert read(library / 'README.pt-BR.md') == before


def test_the_website_home_shows_the_tracks(cli, tracked):
    code, r = cli('build', 'site', '--library', tracked, '--out', tracked / '_site')
    home = read(tracked / '_site' / 'docs' / 'index.md')
    assert code == 0 and '## 🧭 Trilhas' in home
    assert f'[Python do zero (exemplo de teste)](created-books/{FIRST}/README.md)' in home


# ---------- nothing of the original in an improved book ----------

ORIGINAL = ('Neste curso você vai aprender que o controle de versão guarda cada mudança do projeto '
            'e permite voltar no tempo sempre que algo der errado no seu código.')


@pytest.fixture
def improved(book, tmp_path):
    data = load(book / 'book.yaml')
    data.update(origin='improved', original={'title': 'Curso X', 'kind': 'notion', 'where': 'notion'},
                promise={'goal': 1, 'audience': 1, 'level': 1, 'sequence': 1})
    for ch in data['chapters']:
        ch['sources_original'] = ['Aula 1']
    save(book / 'book.yaml', data)
    source = tmp_path / 'sources'
    source.mkdir()
    (source / '01-aula-1.md').write_text(f'# Aula 1\n\n{ORIGINAL}\n\n```bash\ngit init\ngit add .\n'
                                         'git commit -m "primeiro commit do projeto de receitas da ana"\n```\n',
                                         encoding='utf-8')
    return book, source


def test_text_copied_from_the_original_is_an_error(cli, improved):
    book, source = improved
    (book / 'research' / 'c01.md').write_text('# Pesquisa\n\nAnotação: ' + ORIGINAL + '\n', encoding='utf-8')
    code, r = cli('audit', '--book', book, '--original', source)
    assert code == 1 and any('research/c01.md' in e and 'copied from the original' in e for e in r['errors']), r
    assert any('neste curso você vai aprender que o controle de versão' in e for e in r['errors'])


def test_code_and_short_overlaps_are_not_copies(cli, improved):
    book, source = improved
    edit(book / 'chapters' / '01-listas.md', '## Listas',
         '## Listas\n\nO controle de versão guarda cada mudança.\n\n```bash\ngit init\ngit add .\n'
         'git commit -m "primeiro commit do projeto de receitas da ana"\n```')
    code, r = cli('audit', '--book', book, '--original', source)
    assert not any('copied from the original' in e for e in r['errors']), r


def test_an_improved_book_audited_without_the_original_gets_a_reminder(cli, improved):
    book, _ = improved
    code, r = cli('audit', '--book', book)
    assert any('--original' in w for w in r['warnings']), r
    code, r = cli('audit', 1, '--book', book)  # a single chapter while writing: no reminder yet
    assert not any('--original' in w for w in r['warnings'])


def test_a_created_book_needs_no_original(cli, book):
    code, r = cli('audit', '--book', book)
    assert code == 0 and not any('--original' in w for w in r['warnings'])
