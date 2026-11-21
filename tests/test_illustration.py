"""illustration.py: the checks for SVG illustrations drawn by hand (analogies, imagined scenes)."""
import pytest
from conftest import edit

CHAPTER = 'chapters/01-listas.md'
GOOD = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 420" role="img">
  <title>A lista é uma fileira de gavetas numeradas a partir de 0</title>
  <rect width="960" height="420" fill="#FAF9F6"/>
  <rect x="120" y="140" width="200" height="160" rx="12" fill="#EAF1FF" stroke="#1F4E9C" stroke-width="3"/>
  <rect x="380" y="140" width="200" height="160" rx="12" fill="#EAF1FF" stroke="#1F4E9C" stroke-width="3"/>
  <circle cx="220" cy="220" r="10" fill="#2B2B33"/>
  <path d="M 340 220 L 370 220" stroke="#55555F" stroke-width="3" fill="none"/>
  <text x="220" y="330" font-size="20" fill="#2B2B33" text-anchor="middle">gaveta 0</text>
  <text x="480" y="330" font-size="20" fill="#2B2B33" text-anchor="middle">gaveta 1</text>
</svg>
'''


def write(book, name, text):
    path = book / 'img' / name
    path.write_text(text, encoding='utf-8')
    return path


def check(cli, book, name='c01-gavetas.svg'):
    return cli('illustration', book / 'img' / name, '--book', book)


def test_a_simple_illustration_passes(cli, book):
    write(book, 'c01-gavetas.svg', GOOD)
    code, r = check(cli, book)
    assert code == 0 and r == {'ok': True, 'errors': [], 'warnings': []}, r


ERRORS = [
    ('not xml', lambda s: s.replace('</svg>', ''), 'not valid SVG'),
    ('no viewBox', lambda s: s.replace(' viewBox="0 0 960 420"', ''), 'viewBox'),
    ('no title', lambda s: s.replace('<title>A lista é uma fileira de gavetas numeradas a partir de 0</title>', ''),
     '<title>'),
    ('embedded image', lambda s: s.replace('</svg>', '<image href="foto.jpg" width="10" height="10"/></svg>'),
     '<image>'),
    ('script', lambda s: s.replace('</svg>', '<script>alert(1)</script></svg>'), '<script>'),
    ('foreign object', lambda s: s.replace('</svg>', '<foreignObject width="9" height="9"/></svg>'),
     '<foreignObject>'),
    ('event handler', lambda s: s.replace('<circle ', '<circle onclick="x()" '), 'onclick'),
    ('external link', lambda s: s.replace('</svg>', '<use href="https://x.org/a.svg#b"/></svg>'), 'external'),
    ('external style', lambda s: s.replace('</svg>', '<style>@import url(https://x.org/a.css);</style></svg>'),
     'external'),
    ('too wide', lambda s: s.replace('0 0 960 420', '0 0 1400 420'), 'wider than 960'),
]


@pytest.mark.parametrize('case, change, message', ERRORS, ids=[e[0] for e in ERRORS])
def test_each_error(cli, book, case, change, message):
    write(book, 'c01-gavetas.svg', change(GOOD))
    code, r = check(cli, book)
    assert code == 1 and any(message in e for e in r['errors']), r


def test_the_small_reading_profile_is_narrower(cli, book):
    from conftest import load, save
    data = load(book / 'book.yaml')
    data['choices']['reading'] = 'small'
    save(book / 'book.yaml', data)
    write(book, 'c01-gavetas.svg', GOOD)
    code, r = check(cli, book)
    assert code == 1 and any('wider than 480' in e for e in r['errors']), r


WARNINGS = [
    ('color outside the palette', lambda s: s.replace('#EAF1FF', '#FF00AA', 1), 'outside the book palette'),
    ('too many shapes', lambda s: s.replace('</svg>', '<circle cx="1" cy="1" r="1"/>' * 60 + '</svg>'),
     'shapes'),
    ('too many labels', lambda s: s.replace('</svg>', '<text x="1" y="1">a</text>' * 6 + '</svg>'), 'labels'),
    ('long label', lambda s: s.replace('gaveta 0', 'esta é a primeira gaveta da fileira'), 'words'),
]


@pytest.mark.parametrize('case, change, message', WARNINGS, ids=[w[0] for w in WARNINGS])
def test_each_warning(cli, book, case, change, message):
    write(book, 'c01-gavetas.svg', change(GOOD))
    code, r = check(cli, book)
    assert code == 0 and any(message in w for w in r['warnings']), r


def test_a_missing_file_is_an_error(cli, book):
    code, r = check(cli, book, 'c01-nada.svg')
    assert code == 1 and 'not found' in r['error']


def use_in_chapter(book, name):
    edit(book / CHAPTER, 'Guardar 40 notas', f'![Gavetas numeradas](../img/{name})\n\nGuardar 40 notas')


def test_the_audit_checks_illustrations_in_the_chapter(cli, book):
    write(book, 'c01-gavetas.svg', GOOD.replace('</svg>', '<script>alert(1)</script></svg>'))
    use_in_chapter(book, 'c01-gavetas.svg')
    code, r = cli('audit', 1, '--book', book)
    assert code == 1 and any('c01-gavetas.svg' in e and '<script>' in e for e in r['errors']), r
    write(book, 'c01-gavetas.svg', GOOD)
    code, r = cli('audit', 1, '--book', book)
    assert code == 0 and not r['errors'], r


def test_the_audit_leaves_diagrams_from_a_spec_alone(cli, book):
    # c01-lista.svg comes from img/_source/c01-lista.yaml: diagram.py drew it, illustration.py does not check it
    code, r = cli('audit', 1, '--book', book)
    assert code == 0 and not any('c01-lista.svg' in e for e in r['errors'])
