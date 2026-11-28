"""ingest.py: every input type, the section split, Docling and its fallbacks."""
import json
import os
import subprocess
import sys
import zipfile

import ingest
import pytest
from conftest import read


def run(cli, source, out, *args):
    return cli('ingest', source, '--out', out, *args)


def make_pdf(path, pages):
    """A minimal valid PDF with one line of text per page, written byte by byte."""
    objs = ['<< /Type /Catalog /Pages 2 0 R >>',
            '<< /Type /Pages /Kids [' + ' '.join(f'{3 + 2 * i} 0 R' for i in range(len(pages)))
            + f'] /Count {len(pages)} >>']
    font = 3 + 2 * len(pages)
    for i, text in enumerate(pages):
        stream = f'BT /F1 12 Tf 20 100 Td ({text}) Tj ET'
        objs.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Contents {4 + 2 * i} 0 R '
                    f'/Resources << /Font << /F1 {font} 0 R >> >> >>')
        objs.append(f'<< /Length {len(stream)} >>\nstream\n{stream}\nendstream')
    objs.append('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
    body, offsets = '%PDF-1.4\n', []
    for n, obj in enumerate(objs, 1):
        offsets.append(len(body))
        body += f'{n} 0 obj\n{obj}\nendobj\n'
    xref = len(body)
    body += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n' + ''.join(f'{o:010d} 00000 n \n' for o in offsets)
    body += f'trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'
    path.write_bytes(body.encode('latin-1'))


def make_epub(path):
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('mimetype', 'application/epub+zip')
        z.writestr('META-INF/container.xml', '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:'
                   'xmlns:container" version="1.0"><rootfiles><rootfile full-path="OEBPS/content.opf" '
                   'media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr('OEBPS/content.opf', '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" '
                   'version="3.0"><manifest><item id="b" href="b.xhtml"/><item id="a" href="a.xhtml"/></manifest>'
                   '<spine><itemref idref="a"/><itemref idref="b"/></spine></package>')
        z.writestr('OEBPS/a.xhtml', '<html><body><h1>Capítulo Um</h1><p>Primeiro.</p></body></html>')
        z.writestr('OEBPS/b.xhtml', '<html><body><h1>Capítulo Dois</h1><p>Segundo.</p></body></html>')


def test_markdown_is_split_at_headings_up_to_the_level(cli, tmp_path):
    src = tmp_path / 'aula.md'
    src.write_text('Prefácio curto.\n\n# Parte 1\n\nTexto.\n\n## Seção 1.1\n\nMais.\n\n```bash\n# não é título\n```\n'
                   '\n# Parte 2\n\nFim.\n', encoding='utf-8')
    code, r = run(cli, src, tmp_path / 'out')
    assert code == 0 and r['engine'] == 'text'
    assert [s['title'] for s in r['sections']] == ['(intro)', 'Parte 1', 'Seção 1.1', 'Parte 2']
    assert '# não é título' in read(tmp_path / 'out' / r['sections'][2]['file'])
    assert json.loads(read(tmp_path / 'out' / 'outline.json'))['total_words'] == r['total_words']
    code, r = run(cli, src, tmp_path / 'out', '--level', 1)
    assert [s['title'] for s in r['sections']] == ['(intro)', 'Parte 1', 'Parte 2']
    assert len([f for f in os.listdir(tmp_path / 'out') if f.endswith('.md')]) == 3, 'stale sections left'


def test_plain_text_without_headings_is_one_section(cli, tmp_path):
    (tmp_path / 'notas.txt').write_text('Só texto, sem títulos.', encoding='utf-8')
    code, r = run(cli, tmp_path / 'notas.txt', tmp_path / 'out')
    assert [s['title'] for s in r['sections']] == ['(intro)']


NOVEL = ('1\n\nA MÃO E A LUVA\n\nMachado de Assis\n\nI\n\nO fim da carta\n\n- Mas que pretendes fazer?\n\n2\n\n'
         'Texto do primeiro.\n\nII\n\nUm roupão\n\nTexto do segundo.\n\n3\n\nIII\n\n11\n\nNa chácara\n\n'
         'Texto do terceiro.\n')


def test_chapters_marked_only_by_roman_numerals_become_sections(cli, tmp_path):
    """An EPUB made from a PDF (A mão e a luva, from the Biblioteca Nacional) had no headings: each chapter
    starts with a line holding only its number, then its title; lone page numbers are not chapters."""
    (tmp_path / 'romance.md').write_text(NOVEL, encoding='utf-8')
    code, r = run(cli, tmp_path / 'romance.md', tmp_path / 'out')
    assert [s['title'] for s in r['sections']] == ['(intro)', 'I. O fim da carta', 'II. Um roupão', 'III. Na chácara']
    assert 'Texto do segundo' in read(tmp_path / 'out' / r['sections'][2]['file'])
    assert any('chapter numbers' in w for w in r['warnings']), r['warnings']


def test_a_few_roman_numerals_out_of_order_are_not_chapters(cli, tmp_path):
    (tmp_path / 'notas.md').write_text('Item\n\nII\n\nTexto.\n\nV\n\nMais.\n', encoding='utf-8')
    code, r = run(cli, tmp_path / 'notas.md', tmp_path / 'out')
    assert [s['title'] for s in r['sections']] == ['(intro)']


def test_a_folder_of_pages_in_name_order(cli, tmp_path):
    pages = tmp_path / 'notion'
    pages.mkdir()
    (pages / '02 Variáveis.md').write_text('Guardam valores.', encoding='utf-8')
    (pages / '01 Introdução.md').write_text('# Introdução\n\nPor que programar.', encoding='utf-8')
    (pages / 'imagem.png').write_bytes(b'x')
    code, r = run(cli, pages, tmp_path / 'out')
    assert r['engine'] == 'folder' and [s['title'] for s in r['sections']] == ['Introdução', '02 Variáveis']


def test_an_empty_folder_is_reported(cli, tmp_path):
    (tmp_path / 'vazia').mkdir()
    code, r = run(cli, tmp_path / 'vazia', tmp_path / 'out')
    assert code == 1 and 'no .md or .txt' in r['error']


def test_html_keeps_headings_lists_code_emphasis_and_links():
    md = ingest.html_to_md('<html><head><style>x{}</style></head><body><h2>Título</h2><p>Um <b>forte</b> e '
                           '<i>leve</i> com <code>len()</code> e <a href="https://ex.org">link</a>.</p>'
                           '<ul><li>um</li><li>dois</li></ul><pre>print(1)\nprint(2)</pre>'
                           '<script>alert(1)</script></body></html>')
    assert '## Título' in md and '**forte**' in md and '*leve*' in md and '`len()`' in md
    assert '[link](https://ex.org)' in md and '- um' in md and '```\nprint(1)\nprint(2)\n```' in md
    assert 'alert' not in md and 'x{}' not in md


def test_an_html_file(cli, tmp_path):
    (tmp_path / 'p.html').write_text('<h1>Página</h1><p>Conteúdo.</p>', encoding='utf-8')
    code, r = run(cli, tmp_path / 'p.html', tmp_path / 'out')
    assert r['engine'] == 'html' and r['sections'][0]['title'] == 'Página'


def test_an_epub_in_reading_order(cli, tmp_path):
    make_epub(tmp_path / 'livro.epub')
    code, r = run(cli, tmp_path / 'livro.epub', tmp_path / 'out')
    assert r['engine'] == 'epub' and [s['title'] for s in r['sections']] == ['Capítulo Um', 'Capítulo Dois']


def test_a_docx_through_pandoc(cli, tmp_path):
    from common import pandoc_path
    (tmp_path / 'a.md').write_text('# Apostila\n\nTexto da apostila.\n', encoding='utf-8')
    subprocess.run([pandoc_path(), str(tmp_path / 'a.md'), '-o', str(tmp_path / 'a.docx')], check=True)
    code, r = run(cli, tmp_path / 'a.docx', tmp_path / 'out', '--engine', 'basic')
    assert code == 0 and r['engine'] == 'pandoc' and r['sections'][0]['title'] == 'Apostila'


def test_a_broken_docx_is_reported(cli, tmp_path):
    (tmp_path / 'quebrado.docx').write_bytes(b'not a docx')
    code, r = run(cli, tmp_path / 'quebrado.docx', tmp_path / 'out', '--engine', 'basic')
    assert code == 1 and 'pandoc could not read' in r['error']


def test_a_pdf_without_docling_falls_back_to_plain_text_with_a_warning(cli, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, 'docling_command', lambda: None)
    make_pdf(tmp_path / 'lista.pdf', ['Lista de exercicios um', 'Segunda pagina'])
    code, r = run(cli, tmp_path / 'lista.pdf', tmp_path / 'out')
    assert code == 0 and r['engine'] == 'pdf-text' and [s['title'] for s in r['sections']] == ['p. 1', 'p. 2']
    assert 'Lista de exercicios um' in read(tmp_path / 'out' / r['sections'][0]['file'])
    assert any('Docling keeps them' in w for w in r['warnings'])
    assert any('scanned' in w for w in r['warnings'])  # a few words per page looks like a scan


@pytest.fixture
def fake_docling(tmp_path, monkeypatch):
    """A stand-in for the Docling command line: writes a Markdown file to the --output folder."""
    script = tmp_path / 'fake_docling.py'
    script.write_text('import sys, os\nout = sys.argv[sys.argv.index("--output") + 1]\n'
                      'open(os.path.join(out, "doc.md"), "w").write("# Pela Docling\\n\\nTabela preservada.\\n")\n')
    monkeypatch.setattr(ingest, 'docling_command', lambda: [sys.executable, str(script)])


def test_a_pdf_with_docling(cli, tmp_path, fake_docling):
    make_pdf(tmp_path / 'a.pdf', ['texto'])
    code, r = run(cli, tmp_path / 'a.pdf', tmp_path / 'out')
    assert code == 0 and r['engine'] == 'docling' and r['sections'][0]['title'] == 'Pela Docling'


def test_basic_engine_never_uses_docling(cli, tmp_path, fake_docling):
    make_pdf(tmp_path / 'a.pdf', ['texto de uma pagina'])
    code, r = run(cli, tmp_path / 'a.pdf', tmp_path / 'out', '--engine', 'basic')
    assert r['engine'] == 'pdf-text'


def test_docling_failure_is_reported(cli, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, 'docling_command', lambda: [sys.executable, '-c', 'import sys; sys.exit(2)'])
    make_pdf(tmp_path / 'a.pdf', ['x'])
    code, r = run(cli, tmp_path / 'a.pdf', tmp_path / 'out')
    assert code == 1 and 'Docling could not convert' in r['error']


@pytest.mark.parametrize('name, args, message', [
    ('slides.pptx', [], 'need Docling'),
    ('a.pdf', ['--engine', 'docling'], 'Docling is not installed'),
    ('a.xyz', [], 'unsupported file type'),
])
def test_what_cannot_be_read_without_docling(cli, tmp_path, monkeypatch, name, args, message):
    monkeypatch.setattr(ingest, 'docling_command', lambda: None)
    (tmp_path / name).write_bytes(b'x')
    code, r = run(cli, tmp_path / name, tmp_path / 'out', *args)
    assert code == 1 and message in r['error']


def test_a_missing_source(cli, tmp_path):
    code, r = run(cli, tmp_path / 'nada.md', tmp_path / 'out')
    assert code == 1 and 'not found' in r['error']


def test_an_empty_material(cli, tmp_path):
    (tmp_path / 'vazio.md').write_text('   \n', encoding='utf-8')
    code, r = run(cli, tmp_path / 'vazio.md', tmp_path / 'out')
    assert code == 1 and 'has no text' in r['error']


def test_a_big_section_is_flagged(cli, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, 'BIG_SECTION', 5)
    (tmp_path / 'a.md').write_text('# Longa\n\n' + 'palavra ' * 10, encoding='utf-8')
    code, r = run(cli, tmp_path / 'a.md', tmp_path / 'out')
    assert any('read it in parts' in w for w in r['warnings'])


def test_a_web_page(cli, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest, 'fetch', lambda url: (b'<h1>Docs</h1><p>Oficial.</p>', 'text/html; charset=utf-8'))
    code, r = run(cli, 'https://example.org/docs', tmp_path / 'out')
    assert r['engine'] == 'html' and r['sections'][0]['title'] == 'Docs'


def test_a_pdf_at_a_web_address(cli, tmp_path, monkeypatch):
    make_pdf(tmp_path / 'remoto.pdf', ['Arquivo remoto em PDF'])
    monkeypatch.setattr(ingest, 'fetch', lambda url: ((tmp_path / 'remoto.pdf').read_bytes(), 'application/pdf'))
    monkeypatch.setattr(ingest, 'docling_command', lambda: None)
    code, r = run(cli, 'https://example.org/a.pdf', tmp_path / 'out')
    assert r['engine'] == 'pdf-text' and 'Arquivo remoto' in read(tmp_path / 'out' / r['sections'][0]['file'])


def test_a_second_run_replaces_its_own_sections(cli, tmp_path):
    (tmp_path / 'a.md').write_text('# Um\n\nx\n\n# Dois\n\ny\n', encoding='utf-8')
    run(cli, tmp_path / 'a.md', tmp_path / 'out')
    (tmp_path / 'a.md').write_text('# Só um\n\nx\n', encoding='utf-8')
    code, r = run(cli, tmp_path / 'a.md', tmp_path / 'out')
    assert code == 0 and sorted(os.listdir(tmp_path / 'out')) == ['01-so-um.md', 'outline.json']


def test_a_folder_with_chapters_is_never_emptied(cli, tmp_path):
    chapters = tmp_path / 'chapters'
    chapters.mkdir()
    (chapters / '01-listas.md').write_text('# 1. Listas\n', encoding='utf-8')
    (tmp_path / 'a.md').write_text('# Um\n\nx\n', encoding='utf-8')
    code, r = run(cli, tmp_path / 'a.md', chapters)
    assert code == 1 and 'use an empty --out' in r['error'] and (chapters / '01-listas.md').exists()


def test_a_huge_download_is_refused(monkeypatch, capsys):
    class Response:
        headers = {'Content-Type': 'text/html'}

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, size=-1):
            return b'x' * 20
    monkeypatch.setattr(ingest, 'MAX_DOWNLOAD', 10)
    monkeypatch.setattr(ingest.urllib.request, 'urlopen', lambda request, timeout: Response())
    with pytest.raises(SystemExit):
        ingest.fetch('https://example.org/big')
    assert 'larger than 50 MB' in capsys.readouterr().out


def test_an_epub_that_unpacks_to_a_huge_part_is_refused(cli, tmp_path, monkeypatch):
    make_epub(tmp_path / 'livro.epub')
    monkeypatch.setattr(ingest, 'MAX_EPUB_PART', 50)
    code, r = run(cli, tmp_path / 'livro.epub', tmp_path / 'out')
    assert code == 1 and 'not a normal EPUB' in r['error']
