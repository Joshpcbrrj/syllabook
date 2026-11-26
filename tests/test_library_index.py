"""The library's index by track, and the audit that keeps the original of an improved book out of it."""
import re
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
    # without the website and EPUB links next to each book, the track reads in order
    plain = re.sub(r' \(\[Ler no site\]\([^)]*\) · \[EPUB\]\([^)]*\)\)', '', block)
    assert (f'- **Python:** [Python do zero (exemplo de teste)](created-books/{FIRST}/) → '
            '[Funções em Python](improved-materials/funcoes-em-python/)') in plain
    assert '- **Outros livros:** [Violão básico](created-books/violao-basico/)' in plain
    assert 'Python from scratch' not in block  # a translation is listed with its own collection, not in the track
    assert '## 🧭 Tracks' in read(tracked / 'README.md')


def test_the_front_page_opens_with_a_link_to_each_folder_and_its_book_count(cli, tracked):
    cli('build', 'lists', '--library', tracked)
    block = read(tracked / 'README.pt-BR.md').split('<!-- tracks:start -->')[1].split('<!-- tracks:end -->')[0]
    assert block.index('## 📂 Pastas') < block.index('## 🧭 Trilhas')
    assert '| [📗 Livros criados](created-books/README.pt-BR.md) | 2 |' in block
    assert '| [🔁 Materiais aprimorados](improved-materials/README.pt-BR.md) | 1 |' in block
    assert '| [🌐 Livros traduzidos](translated-books/README.pt-BR.md) | 1 |' in block
    assert '| [📗 Created books](created-books/) | 2 |' in read(tracked / 'README.md')


def test_a_track_name_from_library_yaml(cli, tracked):
    settings = load(tracked / 'library.yaml')
    settings['tracks'] = {'python': 'Programação em Python'}
    save(tracked / 'library.yaml', settings)
    cli('build', 'lists', '--library', tracked)
    assert '- **Programação em Python:**' in read(tracked / 'README.pt-BR.md')


def test_no_tracks_still_lists_every_book_with_its_site_and_epub(cli, library):
    cli('build', 'lists', '--library', library)
    home = read(library / 'README.pt-BR.md')
    assert '## 🧭 Trilhas' not in home and '## 📚 Livros' in home
    assert ('- [Python do zero (exemplo de teste)](created-books/python-do-zero-teste/) '
            '([Ler no site](https://exemplo.github.io/minha-biblioteca/created-books/python-do-zero-teste/) · '
            '[EPUB](https://github.com/exemplo/minha-biblioteca/releases/download/epubs/python-do-zero-teste.epub))'
            ) in home


def test_tracks_on_the_front_page_have_the_site_and_epub_next_to_each_book(cli, tracked):
    cli('build', 'lists', '--library', tracked)
    home = read(tracked / 'README.md')
    assert '## 🧭 Tracks' in home and '([Read online](https://' in home and '· [EPUB](https://' in home


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


def test_the_same_source_link_is_not_a_copy(cli, improved):
    book, source = improved
    url = 'https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/'
    with open(source / '01-aula-1.md', 'a', encoding='utf-8') as f:
        f.write(f'\nFonte: <{url}> e [o guia]({url}).\n')
    edit(book / 'chapters' / '01-listas.md', '## Listas', f'## Listas\n\nVeja [a documentação]({url}) e {url}.')
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
