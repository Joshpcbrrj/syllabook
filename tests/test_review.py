"""Reviewing a finished book: the diagnosis, the new edition and the review dates in the library lists."""
import datetime

import pytest
from conftest import edit, load, read, save

TODAY = datetime.date.today()


def change(book, **fields):
    data = load(book / 'book.yaml')
    data.update(fields)
    save(book / 'book.yaml', data)


def test_review_of_a_book_in_good_shape(cli, book):
    change(book, review_by=f'{TODAY.year + 1}-12')
    code, r = cli('book', 'review', '--book', book)
    assert code == 0, r
    assert r['edition'] == '1.0' and r['review_by'] == f'{TODAY.year + 1}-12' and r['due'] is False
    assert r['stale_sources'] == [] and r['audit'] == {'errors': [], 'warnings': []}
    assert 'issues' in r['next']  # it reminds to read the reported errors too


def test_review_lists_what_needs_work(cli, book):
    data = load(book / 'book.yaml')
    data['sources'].append({'title': 'Old docs', 'url': 'https://example.org', 'checked': '2020-01-10'})
    data['review_by'] = '2021-01'
    save(book / 'book.yaml', data)
    edit(book / 'chapters' / '01-listas.md', '## Listas', '## Listas\n\n<!-- TODO: x -->')
    code, r = cli('book', 'review', '--book', book)
    assert code == 0 and r['due'] is True
    assert r['stale_sources'] == [{'title': 'Old docs', 'url': 'https://example.org', 'checked': '2020-01-10'}]
    assert any('TODO' in e for e in r['audit']['errors'])


def test_edition_records_the_new_edition(cli, book):
    code, r = cli('book', 'edition', '1.1', '--summary', 'Portas em 127.0.0.1 e links corrigidos.',
                  '--review-by', f'{TODAY.year + 1}-06', '--book', book)
    assert code == 0 and r == {'saved': True, 'edition': '1.1', 'reviewed_on': TODAY.isoformat(),
                               'review_by': f'{TODAY.year + 1}-06'}
    data = load(book / 'book.yaml')
    assert data['edition'] == '1.1' and data['reviewed_on'] == TODAY.isoformat()
    assert data['editions'][-1] == {'edition': '1.1', 'date': TODAY.isoformat(),
                                    'summary': 'Portas em 127.0.0.1 e links corrigidos.'}
    code, r = cli('book', 'validate', book / 'book.yaml')
    assert code == 0, r


@pytest.mark.parametrize('args, message', [
    (['1.0', '--summary', 'x'], 'must be newer than 1.0'),
    (['0.9', '--summary', 'x'], 'must be newer than 1.0'),
    (['1.1'], '--summary is required'),
    (['um', '--summary', 'x'], 'like 1.1 or 2.0'),
    (['1.1', '--summary', 'x', '--review-by', 'logo'], 'YYYY-MM'),
])
def test_edition_refuses(cli, book, args, message):
    code, r = cli('book', 'edition', *args, '--book', book)
    assert code == 1 and message in r['error'], r


VALIDATION = [
    ('reviewed_on', lambda d: d.update(reviewed_on='ontem'), 'reviewed_on: must be'),
    ('review_by', lambda d: d.update(review_by='2027'), 'review_by: must be'),
    ('editions entry', lambda d: d.update(editions=[{'edition': '1.1'}]),
     'editions[1]: needs edition, date and summary'),
]


@pytest.mark.parametrize('case, fix, message', VALIDATION, ids=[v[0] for v in VALIDATION])
def test_review_fields_are_validated(cli, book, case, fix, message):
    data = load(book / 'book.yaml')
    fix(data)
    save(book / 'book.yaml', data)
    code, r = cli('book', 'validate', book / 'book.yaml')
    assert code == 1 and any(message in e for e in r['errors']), r['errors']


def test_status_says_when_the_review_is_due(cli, book):
    change(book, review_by='2021-01', progress=[{'n': 1, 'summary': 'a'}, {'n': 2, 'summary': 'b'}])
    code, r = cli('book', 'status', '--book', book)
    assert r['review_due'] is True


def test_build_writes_the_editions_in_the_book_readme(cli, book, tmp_path):
    cli('book', 'edition', '1.1', '--summary', 'Portas em 127.0.0.1.', '--book', book)
    cli('build', '--book', book, '--out', tmp_path / 'd', '--no-epub', '--no-zip')
    text = read(book / 'README.md')
    block = text.split('<!-- editions:start -->')[1].split('<!-- editions:end -->')[0]
    assert '## 🗒️ Edições' in block and f'- **1.1** ({TODAY.isoformat()}): Portas em 127.0.0.1.' in block


def test_lists_show_the_edition_and_a_review_that_is_due(cli, library):
    first = library / 'created-books' / 'python-do-zero-teste'
    change(first, edition='1.1', reviewed_on='2026-11-20', review_by='2021-01')
    cli('build', 'lists', '--library', library)
    text = read(library / 'created-books' / 'README.pt-BR.md')
    assert '| Livro | Nível | Capítulos | Edição | EPUB |' in text
    assert '| 1.1 · 2026-11-20 ⏰ |' in text
    change(first, review_by=f'{TODAY.year + 1}-01')
    cli('build', 'lists', '--library', library)
    assert '| 1.1 · 2026-11-20 |' in read(library / 'created-books' / 'README.pt-BR.md')
