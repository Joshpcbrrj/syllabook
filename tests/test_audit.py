"""audit.py: every check, per chapter and for the whole book, in both reading profiles."""
import os
import shutil

import pytest
from conftest import edit, load, save

CHAPTER = os.path.join('chapters', '01-listas.md')
BLOCK = ('```python\nnotas = [7.5, 8.0, 6.5]\nmaior = max(notas)\nmenor = min(notas)\n'
         'print(maior, menor)\n```\n\n## 🏋️ Pratique')


def audit(cli, book, *args):
    return cli('audit', *args, '--book', book)


@pytest.mark.parametrize('file, old, new, message', [
    ('README.md', '## 📇 O livro numa página', '## Resumo', 'no "O livro numa página" section'),
    (os.path.join('chapters', '00-como-estudar-este-livro.md'), '(../img/c00-o-livro-numa-pagina.svg)',
     '(../img/c01-lista.svg)', 'chapter 0: "O livro numa página"'),
    (os.path.join('img', '_source', 'c00-o-livro-numa-pagina.yaml'), 'type: cards', 'type: boxes',
     'must be drawn by diagram.py from a cards spec'),
])
def test_the_book_on_one_page_is_required_in_the_readme_and_chapter_0(cli, book, file, old, new, message):
    edit(book / file, old, new)
    code, r = audit(cli, book)
    assert code == 1 and any(message in e for e in r['errors']), r['errors']


def test_the_sample_book_is_ready(cli, book):
    code, r = audit(cli, book)
    assert code == 0 and r['ready'] and not r['errors'] and not r['warnings'], r
    code, r = audit(cli, book, 1)
    assert code == 0 and r['scope'] == 'chapter 1'


ERRORS = [
    ('placeholder', '## Listas', '## Listas\n\n<!-- TODO: explain -->', 'TODO placeholder'),
    ('missing section', '## 🧠 Revisão rápida', '## Revisão', 'missing section "Revisão rápida"'),
    ('code without comment', '## 🏋️ Pratique', BLOCK, 'no comment explaining why'),
    ('long code line', 'quantidade = len(notas)', 'quantidade = len(notas)' + ' + 0' * 25, 'limit 80'),
    ('image without alt', '![A lista notas com os índices 0, 1 e 2 e os valores 7,5, 8,0 e 6,5]', '![]',
     'image without alt text'),
    ('missing image', '../img/c01-lista.svg', '../img/nao-existe.svg', 'image not found'),
    ('missing image, alt with brackets', '![A lista notas com os índices 0, 1 e 2 e os valores 7,5, 8,0 e 6,5]'
     '(../img/c01-lista.svg)', '![A lista notas = [7.5, 8.0, 6.5]](../img/nao-existe.svg)', 'image not found'),
    ('broken link', '## 📚 Fontes', 'Veja o [capítulo 5](05-nao-existe.md).\n\n## 📚 Fontes', 'missing file'),
    ('no blank line after summary', '<summary>Ver resposta</summary>\n\n4.', '<summary>Ver resposta</summary>\n4.',
     'after <summary>'),
    ('no blank line before /details', 'maior valor.\n\n</details>', 'maior valor.\n</details>', 'before </details>'),
    ('unclosed code block', '```text\n3\n```', '```text\n3\n', 'never closed'),
    ('placeholder read as a tag', '## 📚 Fontes', 'Cole aqui: <sua resposta>.\n\n## 📚 Fontes',
     '"<sua resposta>" outside code'),
]


@pytest.mark.parametrize('case, old, new, message', ERRORS, ids=[e[0] for e in ERRORS])
def test_each_chapter_error(cli, book, case, old, new, message):
    edit(book / CHAPTER, old, new)
    code, r = audit(cli, book, 1)
    assert code == 1 and not r['ready'] and any(message in e for e in r['errors']), r['errors']


WARNINGS = [
    ('long output line', '```text\n3\n```', '```text\n' + 'x ' * 50 + '\n```', 'characters (limit 80)'),
    ('long URL in code', 'quantidade = len(notas)',
     'quantidade = len(notas)  # https://docs.python.org/3/tutorial/datastructures.html#more-on-lists', 'limit 80'),
    ('wide table', '| Item | Em uma frase |\n| --- | --- |',
     '| a | b | c | d | e | f | g |\n| --- | --- | --- | --- | --- | --- | --- |', 'table with 7 columns'),
    ('filler word', 'Guardar 40 notas', 'Basicamente, guardar 40 notas', 'filler word'),
    ('sources without link', '- [The Python Tutorial](https://docs.python.org/3/tutorial/), conferido em 2026-11-20.',
     '- The Python Tutorial', 'has no link'),
]


@pytest.mark.parametrize('case, old, new, message', WARNINGS, ids=[w[0] for w in WARNINGS])
def test_each_chapter_warning(cli, book, case, old, new, message):
    edit(book / CHAPTER, old, new)
    code, r = audit(cli, book, 1)
    assert code == 0 and r['ready'] and any(message in w for w in r['warnings']), r


def test_small_reading_profile_has_stricter_limits(cli, book):
    data = load(book / 'book.yaml')
    data['choices']['reading'] = 'small'
    save(book / 'book.yaml', data)
    # 70 characters: fine on large screens, too long on a 6-inch e-reader
    edit(book / CHAPTER, 'quantidade = len(notas)', 'quantidade = len(notas)' + ' + 0' * 12)
    code, r = audit(cli, book, 1)
    assert code == 1 and any('limit 60' in e for e in r['errors'])


def test_where_we_left_off_is_required_from_chapter_two(cli, book):
    edit(book / 'chapters' / '02-o-laco-for.md', '## De onde paramos', '## Antes')
    code, r = audit(cli, book, 2)
    assert code == 1 and any('De onde paramos' in e for e in r['errors'])


@pytest.mark.parametrize('setup, message', [
    (lambda b: os.remove(b / 'chapters' / 'glossario.md'), 'fixed part missing: Glossário'),
    (lambda b: os.remove(b / 'chapters' / '03-simulado-final.md'), 'fixed part missing: Simulado final'),
    (lambda b: os.remove(b / 'chapters' / '00-como-estudar-este-livro.md'), 'fixed part missing: chapter 0'),
    (lambda b: os.remove(b / 'README.md'), 'README.md missing'),
    (lambda b: os.remove(b / 'chapters' / '02-o-laco-for.md'), 'chapter 2: file missing'),
    (lambda b: edit(b / 'chapters' / 'glossario.md', '# Glossário', '# Glossário\n\n<!-- TODO -->'), 'TODO'),
])
def test_whole_book_errors(cli, book, setup, message):
    setup(book)
    code, r = audit(cli, book)
    assert code == 1 and any(message in e for e in r['errors']), r['errors']


def test_whole_book_warns_about_unused_images_but_ignores_sources_and_credits(cli, book):
    shutil.copy(book / 'img' / 'c01-lista.svg', book / 'img' / 'sobrando.svg')
    os.makedirs(book / 'img' / '_source', exist_ok=True)
    (book / 'img' / '_source' / 'c01-lista.yaml').write_text('type: blocks\n')
    (book / 'img' / 'CREDITS.md').write_text('# Credits\n')
    code, r = audit(cli, book)
    assert code == 0 and r['warnings'] == ['image not used in any chapter: img/sobrando.svg']


def test_improved_book_chapters_must_say_where_they_come_from(cli, book):
    data = load(book / 'book.yaml')
    data['origin'] = 'improved'
    save(book / 'book.yaml', data)
    code, r = audit(cli, book, 1)
    assert code == 1 and any('sources_original' in e for e in r['errors'])


def test_a_chapter_without_its_research_dossier_is_a_warning(cli, book):
    os.remove(book / 'research' / 'c01.md')
    code, r = audit(cli, book, 1)
    assert code == 0 and any('research/c01.md' in w for w in r['warnings']), r


def test_a_translation_needs_no_research_dossier(cli, book):
    os.remove(book / 'research' / 'c01.md')
    data = load(book / 'book.yaml')
    data['translation_of'] = 'python-do-zero-en'
    save(book / 'book.yaml', data)
    code, r = audit(cli, book, 1)
    assert not any('research/' in w for w in r['warnings']), r


def test_a_book_without_any_analogy_is_a_warning(cli, book):
    for path in (book / 'chapters').glob('*.md'):
        text = path.read_text(encoding='utf-8')
        path.write_text(text.replace('💡 **Analogia:**', '💡 **Dica:**'), encoding='utf-8')
    code, r = audit(cli, book)
    assert code == 0 and any('analogy' in w for w in r['warnings']), r


def test_a_photo_without_credit_is_an_error(cli, book):
    (book / 'img' / 'c01-foto.jpg').write_bytes(b'fake')
    edit(book / CHAPTER, 'Guardar 40 notas', '![Uma foto](../img/c01-foto.jpg)\n\nGuardar 40 notas')
    code, r = audit(cli, book, 1)
    assert code == 1 and any('c01-foto.jpg' in e and 'CREDITS.md' in e for e in r['errors']), r
    (book / 'img' / 'CREDITS.md').write_text('# Créditos\n\n- c01-foto.jpg: foto, domínio público\n',
                                             encoding='utf-8')
    code, r = audit(cli, book, 1)
    assert code == 0, r


OPEN_PORT = [
    ('compose short syntax', '```yaml\n# a API na porta 8080\nports:\n  - "8080:80"\n```', '8080:80'),
    ('compose without quotes', '```yaml\n# a API\nports:\n  - 8080:80\n```', '8080:80'),
    ('docker run -p', '```bash\n# sobe o nginx\ndocker run -d -p 8080:80 nginx\n```', '8080:80'),
    ('docker run --publish', '```bash\n# sobe o nginx\ndocker run -d --publish=5432:5432 postgres\n```', '5432:5432'),
]


@pytest.mark.parametrize('case, block, port', OPEN_PORT, ids=[o[0] for o in OPEN_PORT])
def test_a_port_open_on_every_interface_is_a_warning(cli, book, case, block, port):
    edit(book / CHAPTER, '## 🏋️ Pratique', block + '\n\n## 🏋️ Pratique')
    code, r = audit(cli, book, 1)
    assert code == 0 and any(port in w and '127.0.0.1' in w for w in r['warnings']), r


@pytest.mark.parametrize('block', [
    '```yaml\n# só nesta máquina\nports:\n  - "127.0.0.1:8080:80"\n```',
    '```bash\n# só nesta máquina\ndocker run -d -p 127.0.0.1:8080:80 nginx\n```',
    '```bash\n# aberta de propósito: o servidor recebe acessos da rede\ndocker run -d -p 0.0.0.0:80:80 nginx\n```',
    '```text\n0.0.0.0:8080->80/tcp\n```',
    '```bash\n# mapeia a porta\nssh -p 2222 ana@servidor\n```',
], ids=['compose local', 'run local', 'explicit 0.0.0.0', 'output', 'ssh -p'])
def test_local_explicit_or_unrelated_ports_are_fine(cli, book, block):
    edit(book / CHAPTER, '## 🏋️ Pratique', block + '\n\n## 🏋️ Pratique')
    code, r = audit(cli, book, 1)
    assert not any('127.0.0.1' in w for w in r['warnings']), r



def test_an_image_used_only_in_the_readme_is_not_an_orphan(cli, book):
    shutil.copy(book / 'img' / 'c01-lista.svg', book / 'img' / 'c00-cola.svg')
    readme = book / 'README.md'
    readme.write_text(readme.read_text(encoding='utf-8') + '\n![A cola do livro](img/c00-cola.svg)\n',
                      encoding='utf-8')
    code, r = audit(cli, book)
    assert not any('c00-cola.svg' in w for w in r['warnings']), r
