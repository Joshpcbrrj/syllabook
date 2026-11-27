"""images.py: free-license photos from Wikimedia Commons and screenshots of the book's application."""
import base64
import sys
import types

import images
import pytest

ENIAC = {
    'title': 'File:Eniac.jpg', 'imageinfo': [{
        'thumburl': 'https://upload.wikimedia.org/eniac-1280.jpg', 'mime': 'image/jpeg', 'width': 1280,
        'height': 960, 'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Eniac.jpg',
        'extmetadata': {'LicenseShortName': {'value': 'Public domain'},
                        'Artist': {'value': '<a href="x">U.S. Army</a> Photo'},
                        'LicenseUrl': {'value': ''}}}]}
LOGO = {
    'title': 'File:Some logo.png', 'imageinfo': [{
        'thumburl': 'https://upload.wikimedia.org/logo.png', 'mime': 'image/png', 'width': 400, 'height': 400,
        'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Some_logo.png',
        'extmetadata': {'LicenseShortName': {'value': 'Logo'}, 'NonFree': {'value': 'true'}}}]}
HOPPER = {
    'title': 'File:Grace Hopper.jpg', 'imageinfo': [{
        'thumburl': 'https://upload.wikimedia.org/hopper-1280.jpg', 'mime': 'image/jpeg', 'width': 1280,
        'height': 1600, 'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Grace_Hopper.jpg',
        'extmetadata': {'LicenseShortName': {'value': 'CC BY-SA 4.0'}, 'Artist': {'value': 'Jane Doe'},
                        'LicenseUrl': {'value': 'https://creativecommons.org/licenses/by-sa/4.0'}}}]}


@pytest.fixture
def commons(monkeypatch):
    """Fake Commons API: returns the pages given, and records downloads instead of fetching.
    Openverse answers with nothing unless a test uses the openverse fixture: tests never go online."""
    state = {'pages': [], 'downloads': []}
    monkeypatch.setattr(images, 'openverse_api', lambda path, params=None: {'results': []})
    monkeypatch.setattr(images, 'api', lambda params: {'query': {'pages': {str(i): p for i, p in
                                                                             enumerate(state['pages'])}}})

    def download(url, path):
        state['downloads'].append(url)
        with open(path, 'wb') as f:
            f.write(b'\xff\xd8 fake jpeg')
    monkeypatch.setattr(images, 'download', download)
    return state


@pytest.mark.parametrize('license_name, free', [
    ('Public domain', True), ('PD-US', True), ('CC0', True), ('CC BY 4.0', True), ('CC BY-SA 3.0', True),
    ('CC BY-NC 4.0', False), ('CC BY-ND 4.0', False), ('Logo', False), ('', False),
])
def test_only_free_licenses_are_accepted(license_name, free):
    assert images.free_license(license_name) is free


@pytest.mark.parametrize('raw, author', [
    ('The original uploader was <a href="x">Piero Sagnibene</a> at Italian Wikipedia .',
     'Piero Sagnibene (Italian Wikipedia)'),
    ('<a href="x">U.S. Army</a> Photo', 'U.S. Army Photo'),
    ('Jane Doe .', 'Jane Doe'),
])
def test_the_author_of_a_commons_image_reads_well_in_a_caption(raw, author):
    assert images.author_name(raw) == author


def test_search_lists_only_free_images_with_their_credit(cli, commons):
    commons['pages'] = [ENIAC, LOGO, HOPPER]
    code, r = cli('images', 'search', 'eniac')
    assert code == 0 and [i['title'] for i in r['results']] == ['File:Eniac.jpg', 'File:Grace Hopper.jpg']
    assert r['results'][0]['author'] == 'U.S. Army Photo' and r['results'][1]['license'] == 'CC BY-SA 4.0'
    assert r['left_out'] == 1


def test_fetch_saves_the_image_and_its_credit(cli, book, commons):
    commons['pages'] = [HOPPER]
    code, r = cli('images', 'fetch', 'File:Grace Hopper.jpg', '--name', 'c02-hopper', '--book', book)
    assert code == 0 and (book / 'img' / 'c02-hopper.jpg').exists()
    credits = (book / 'img' / 'CREDITS.md').read_text(encoding='utf-8')
    assert credits.startswith('# Image credits' + chr(10) * 2 + '- c02-hopper.jpg:') and 'CC BY-SA 4.0' in credits
    assert 'Jane Doe' in credits and 'commons.wikimedia.org' in credits
    assert r['markdown'].startswith('![') and '../img/c02-hopper.jpg' in r['markdown']
    assert 'Jane Doe' in r['caption'] and 'CC BY-SA 4.0' in r['caption']


def test_fetch_refuses_a_non_free_image(cli, book, commons):
    commons['pages'] = [LOGO]
    code, r = cli('images', 'fetch', 'File:Some logo.png', '--name', 'c02-logo', '--book', book)
    assert code == 1 and 'free license' in r['error'] and not commons['downloads']


def test_fetch_of_a_missing_file_is_an_error(cli, book, commons):
    commons['pages'] = [{'title': 'File:Nope.jpg', 'missing': ''}]
    code, r = cli('images', 'fetch', 'File:Nope.jpg', '--name', 'c02-x', '--book', book)
    assert code == 1 and 'not found' in r['error']


def test_a_second_fetch_does_not_repeat_the_credit(cli, book, commons):
    commons['pages'] = [HOPPER]
    cli('images', 'fetch', 'File:Grace Hopper.jpg', '--name', 'c02-hopper', '--book', book)
    cli('images', 'fetch', 'File:Grace Hopper.jpg', '--name', 'c02-hopper', '--book', book)
    credits = (book / 'img' / 'CREDITS.md').read_text(encoding='utf-8')
    assert credits.count('c02-hopper.jpg') == 1


def test_screenshot_without_playwright_explains_what_to_do(cli, book, monkeypatch):
    monkeypatch.setitem(sys.modules, 'playwright', None)
    code, r = cli('images', 'screenshot', 'http://localhost:8080', '--name', 'c05-app', '--book', book)
    assert code == 1 and 'playwright install chromium' in r['error'] and 'ask the user' in r['error']


def test_screenshot_saves_the_page_and_its_credit(cli, book, monkeypatch):
    shots = []

    class Page:
        def goto(self, url, wait_until):
            shots.append(url)

        def screenshot(self, path, full_page):
            open(path, 'wb').write(b'\x89PNG fake')

    class Browser:
        def new_page(self, viewport):
            return Page()

        def close(self):
            pass

    class Playwright:
        chromium = types.SimpleNamespace(launch=lambda: Browser())

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    sync_api = types.ModuleType('playwright.sync_api')
    sync_api.sync_playwright = Playwright
    monkeypatch.setitem(sys.modules, 'playwright', types.ModuleType('playwright'))
    monkeypatch.setitem(sys.modules, 'playwright.sync_api', sync_api)
    code, r = cli('images', 'screenshot', 'http://localhost:8080', '--name', 'c05-app', '--book', book)
    assert code == 0 and shots == ['http://localhost:8080'] and (book / 'img' / 'c05-app.png').exists()
    assert 'c05-app.png' in (book / 'img' / 'CREDITS.md').read_text(encoding='utf-8')


TISUE = {'id': 'abc-123', 'title': 'ENIAC', 'creator': 'Seth Tisue', 'license': 'by-sa', 'license_version': '2.0',
         'license_url': 'https://creativecommons.org/licenses/by-sa/2.0/', 'source': 'flickr', 'mature': False,
         'foreign_landing_url': 'https://www.flickr.com/photos/x/5950309497', 'width': 1024, 'height': 746,
         'url': 'https://live.staticflickr.com/6136/5950309497_b.jpg'}
NC = dict(TISUE, id='nc-1', license='by-nc', title='ENIAC NC')


@pytest.fixture
def openverse(monkeypatch):
    """Fake Openverse API: a search returns the results given; a detail returns the one with that id."""
    state = {'results': [], 'calls': []}

    def call(path, params=None):
        state['calls'].append((path, params))
        if path == 'images/':
            return {'results': state['results']}
        found = [r for r in state['results'] if path == f'images/{r["id"]}/']
        if not found:
            raise images.urllib.error.HTTPError(path, 404, 'Not Found', {}, None)
        return found[0]
    monkeypatch.setattr(images, 'openverse_api', call)
    return state


@pytest.mark.parametrize('code, version, name', [
    ('cc0', '1.0', 'CC0 1.0'), ('pdm', '1.0', 'Public domain'), ('by', '4.0', 'CC BY 4.0'),
    ('by-sa', '2.0', 'CC BY-SA 2.0'), ('by-nc', '2.0', 'CC BY-NC 2.0'),
])
def test_openverse_license_names(code, version, name):
    assert images.license_name(code, version) == name


def test_search_looks_in_commons_and_openverse(cli, commons, openverse):
    commons['pages'] = [ENIAC]
    openverse['results'] = [TISUE, NC]
    code, r = cli('images', 'search', 'eniac')
    assert code == 0 and [i['fetch'] for i in r['results']] == ['File:Eniac.jpg', 'openverse:abc-123']
    ov = r['results'][1]
    assert ov['author'] == 'Seth Tisue' and ov['license'] == 'CC BY-SA 2.0' and ov['via'] == 'Openverse (flickr)'
    assert r['left_out'] == 1
    params = openverse['calls'][0][1]
    assert params['license'] == 'by,by-sa,cc0,pdm' and params['q'] == 'eniac'


def test_search_in_one_source_only(cli, commons, openverse):
    commons['pages'] = [ENIAC]
    openverse['results'] = [TISUE]
    code, r = cli('images', 'search', 'eniac', '--source', 'openverse')
    assert [i['fetch'] for i in r['results']] == ['openverse:abc-123']


def test_search_goes_on_when_a_source_is_down(cli, commons, monkeypatch):
    commons['pages'] = [ENIAC]

    def down(path, params=None):
        raise images.urllib.error.URLError('offline')
    monkeypatch.setattr(images, 'openverse_api', down)
    code, r = cli('images', 'search', 'eniac')
    assert code == 0 and [i['fetch'] for i in r['results']] == ['File:Eniac.jpg'] and r['unavailable'] == ['openverse']


def test_fetch_from_openverse_saves_the_image_and_its_credit(cli, book, commons, openverse):
    openverse['results'] = [TISUE]
    code, r = cli('images', 'fetch', 'openverse:abc-123', '--name', 'c01-eniac', '--book', book)
    assert code == 0 and (book / 'img' / 'c01-eniac.jpg').exists()
    assert commons['downloads'] == [TISUE['url']]
    credits = (book / 'img' / 'CREDITS.md').read_text(encoding='utf-8')
    assert 'Seth Tisue' in credits and 'CC BY-SA 2.0' in credits and 'flickr.com/photos/x' in credits
    assert r['caption'] == 'Seth Tisue, CC BY-SA 2.0, via Openverse (flickr)'


def test_fetch_from_openverse_refuses_a_non_free_image(cli, book, commons, openverse):
    openverse['results'] = [NC]
    code, r = cli('images', 'fetch', 'openverse:nc-1', '--name', 'c01-x', '--book', book)
    assert code == 1 and 'free license' in r['error'] and not commons['downloads']


def test_fetch_from_openverse_of_a_missing_image(cli, book, commons, openverse):
    code, r = cli('images', 'fetch', 'openverse:nope', '--name', 'c01-x', '--book', book)
    assert code == 1 and 'not found' in r['error']


# --- editor: screenshots of VS Code (code-server) ---

class PaletteRows:
    """The palette's list as Playwright sees it: rows with a label, the ones a click would run."""
    def __init__(self, labels, log):
        self.labels, self.log = labels, log

    def count(self):
        return len(self.labels)

    def nth(self, i):
        label, log = self.labels[i], self.log
        text = types.SimpleNamespace(inner_text=lambda: label)
        return types.SimpleNamespace(
            locator=lambda sel: types.SimpleNamespace(count=lambda: 1, first=text),
            click=lambda: log.append(('click', label)))


def fake_playwright(monkeypatch, log):
    class Keyboard:
        def press(self, key):
            log.append(('press', key))

        def type(self, text):
            log.append(('type', text))

    class Page:
        keyboard = Keyboard()
        mouse = types.SimpleNamespace(move=lambda x, y: None)

        def locator(self, selector):
            return PaletteRows([], log)

        def goto(self, url, **kw):
            log.append(('goto', url))

        def wait_for_selector(self, selector, **kw):
            pass

        def wait_for_timeout(self, ms):
            pass

        def screenshot(self, path, full_page):
            open(path, 'wb').write(b'\x89PNG fake')

    class Browser:
        def new_page(self, viewport):
            return Page()

        def close(self):
            pass

    class Playwright:
        chromium = types.SimpleNamespace(launch=lambda: Browser())

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    sync_api = types.ModuleType('playwright.sync_api')
    sync_api.sync_playwright = Playwright
    monkeypatch.setitem(sys.modules, 'playwright', types.ModuleType('playwright'))
    monkeypatch.setitem(sys.modules, 'playwright.sync_api', sync_api)


@pytest.fixture
def lab(tmp_path):
    folder = tmp_path / 'receitas'
    (folder / 'receitas').mkdir(parents=True)
    (folder / 'receitas' / 'bolo.md').write_text('# Bolo\n', encoding='utf-8')
    return folder


def test_editor_without_playwright_explains_what_to_do(cli, book, lab, monkeypatch):
    monkeypatch.setitem(sys.modules, 'playwright', None)
    code, r = cli('images', 'editor', lab, '--name', 'c03-vscode', '--book', book)
    assert code == 1 and 'Playwright' in r['error'] and 'ask the user' in r['error']


def test_editor_without_code_server_or_docker_asks_the_user(cli, book, lab, monkeypatch):
    fake_playwright(monkeypatch, [])
    monkeypatch.setattr(images.shutil, 'which', lambda name: None)
    code, r = cli('images', 'editor', lab, '--name', 'c03-vscode', '--book', book)
    assert code == 1 and 'ask the user' in r['error'] and 'Docker' in r['error']


def test_editor_never_pulls_the_image_without_asking(cli, book, lab, monkeypatch):
    fake_playwright(monkeypatch, [])
    monkeypatch.setattr(images.shutil, 'which', lambda name: '/usr/bin/docker' if name == 'docker' else None)
    runs = []

    def run(cmd, **kw):
        runs.append(cmd)
        return types.SimpleNamespace(returncode=1, stdout='', stderr='No such image')
    monkeypatch.setattr(images.subprocess, 'run', run)
    code, r = cli('images', 'editor', lab, '--name', 'c03-vscode', '--book', book)
    assert code == 1 and 'ask the user first' in r['error']
    assert f'docker pull {images.CODE_SERVER_IMAGE}' in r['error']
    assert all(c[:2] != ['docker', 'pull'] and c[:2] != ['docker', 'run'] for c in runs)


def test_docker_server_is_isolated_and_local_only(lab, tmp_path):
    cmd, url = images.docker_server(str(lab), 8123, str(tmp_path / 'ud'))
    text = ' '.join(cmd)
    assert '-p 127.0.0.1:8123:8080' in text and '--auth none' in text and images.CODE_SERVER_IMAGE in cmd
    assert f'{lab}:/home/coder/receitas' in text and '/home/coder/ud' in text
    assert 'GIT_CONFIG_VALUE_0=*' in text  # safe.directory: the mounted folder belongs to another user
    assert url == 'http://127.0.0.1:8123/?folder=/home/coder/receitas'


def test_editor_settings_are_clean_and_readable(tmp_path):
    images.write_settings(str(tmp_path), dark=False)
    settings = images.json.load(open(tmp_path / 'User' / 'settings.json', encoding='utf-8'))
    assert settings['workbench.colorTheme'] == 'Default Light Modern'
    assert settings['telemetry.telemetryLevel'] == 'off' and settings['security.workspace.trust.enabled'] is False
    images.write_settings(str(tmp_path), dark=True)
    theme = images.json.load(open(tmp_path / 'User' / 'settings.json', encoding='utf-8'))['workbench.colorTheme']
    assert 'Dark' in theme


def test_editor_opens_files_shows_the_view_and_saves_the_screenshot(cli, book, lab, monkeypatch):
    log, stopped = [], []
    fake_playwright(monkeypatch, log)
    monkeypatch.setattr(images, 'start_editor', lambda folder, ud: ('http://127.0.0.1:9/?folder=/x',
                                                                   lambda: stopped.append(True)))
    code, r = cli('images', 'editor', lab, '--name', 'c03-vscode', '--open', 'receitas/bolo.md',
                  '--view', 'scm', '--book', book)
    assert code == 0 and (book / 'img' / 'c03-vscode.png').exists() and stopped == [True]
    assert ('type', 'receitas/bolo.md') in log and ('type', 'View: Show Source Control') in log
    assert log.index(('type', 'receitas/bolo.md')) < log.index(('type', 'View: Show Source Control'))
    credits = (book / 'img' / 'CREDITS.md').read_text(encoding='utf-8')
    assert 'c03-vscode.png' in credits and 'code-server' in credits
    assert 'VS Code (code-server)' in r['caption']


def test_editor_stops_the_server_even_when_the_capture_fails(cli, book, lab, monkeypatch):
    stopped = []
    fake_playwright(monkeypatch, [])
    monkeypatch.setattr(images, 'start_editor', lambda folder, ud: ('http://x', lambda: stopped.append(True)))

    def boom(*a, **k):
        raise RuntimeError('boom')
    monkeypatch.setattr(images, 'drive_editor', boom)
    with pytest.raises(RuntimeError):
        cli('images', 'editor', lab, '--name', 'c03-vscode', '--book', book)
    assert stopped == [True]


def test_editor_refuses_a_folder_that_does_not_exist(cli, book, tmp_path):
    code, r = cli('images', 'editor', tmp_path / 'nope', '--name', 'c03-x', '--book', book)
    assert code == 1 and 'not found' in r['error']


def test_search_skips_openverse_copies_of_commons_images(cli, commons, openverse):
    openverse['results'] = [dict(TISUE, id='wm-1', source='wikimedia'), TISUE]
    code, r = cli('images', 'search', 'eniac')
    assert [i['fetch'] for i in r['results']] == ['openverse:abc-123']
    code, r = cli('images', 'search', 'eniac', '--source', 'openverse')
    assert [i['fetch'] for i in r['results']] == ['openverse:wm-1', 'openverse:abc-123']



# --- the network calls and the code-server process, simulated ---

class FakeResponse:
    def __init__(self, body, kind='image/jpeg'):
        self.body = body
        self.headers = {'Content-Type': kind}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, size=-1):
        return self.body if size < 0 else self.body[:size]


@pytest.mark.parametrize('url, body, kind, message', [
    ('file:///etc/passwd', b'x', 'image/jpeg', 'not an https address'),
    ('http://example.org/a.jpg', b'x', 'image/jpeg', 'not an https address'),
    ('https://example.org/a.jpg', b'<html>', 'text/html', 'not an image'),
    ('https://example.org/a.svg', b'<svg><script>alert(1)</script></svg>', 'image/svg+xml', 'scripts'),
    ('https://example.org/a.svg', b'<svg><rect onload="x()"/></svg>', 'image/svg+xml', 'scripts'),
])
def test_download_refuses_what_is_not_a_safe_image(monkeypatch, tmp_path, capsys, url, body, kind, message):
    monkeypatch.setattr(images.urllib.request, 'urlopen', lambda request, timeout: FakeResponse(body, kind))
    with pytest.raises(SystemExit):
        images.download(url, str(tmp_path / 'a.img'))
    assert message in capsys.readouterr().out and not (tmp_path / 'a.img').exists()


def test_download_refuses_a_huge_image(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(images, 'MAX_IMAGE', 10)
    monkeypatch.setattr(images.urllib.request, 'urlopen', lambda request, timeout: FakeResponse(b'x' * 50))
    with pytest.raises(SystemExit):
        images.download('https://example.org/a.jpg', str(tmp_path / 'a.jpg'))
    assert 'larger than' in capsys.readouterr().out and not (tmp_path / 'a.jpg').exists()


@pytest.mark.parametrize('name', ['../../escape', 'c01/x', 'C01-Upper', '', 'c01 x'])
def test_a_name_that_is_not_a_plain_file_name_is_refused(cli, book, commons, name):
    commons['pages'] = [HOPPER]
    code, r = cli('images', 'fetch', 'File:Grace Hopper.jpg', '--name', name, '--book', book)
    assert code == 1 and 'invalid --name' in r['error'] and not commons['downloads']


def test_screenshot_refuses_a_local_file(cli, book):
    code, r = cli('images', 'screenshot', 'file:///home/user/.ssh/id_rsa', '--name', 'c05-x', '--book', book)
    assert code == 1 and 'only http and https' in r['error']


def test_api_calls_send_who_we_are_and_read_json(monkeypatch, tmp_path):
    seen = []

    def urlopen(request, timeout):
        seen.append(request)
        return FakeResponse(b'{"ok": true}')
    monkeypatch.setattr(images.urllib.request, 'urlopen', urlopen)
    monkeypatch.setattr(images.json, 'load', lambda response: {'ok': response.read() == b'{"ok": true}'})
    assert images.api({'action': 'query'}) == {'ok': True}
    assert images.openverse_api('images/', {'q': 'eniac'}) == {'ok': True}
    images.download('https://example.org/a.jpg', str(tmp_path / 'a.jpg'))
    assert (tmp_path / 'a.jpg').read_bytes() == b'{"ok": true}'
    assert all(r.get_header('User-agent') == images.AGENT for r in seen)
    assert seen[0].full_url.startswith(images.API) and 'format=json' in seen[0].full_url
    assert seen[1].full_url == images.OPENVERSE + 'images/?q=eniac'


def test_wait_until_up(monkeypatch):
    monkeypatch.setattr(images.urllib.request, 'urlopen', lambda url, timeout: FakeResponse(b''))
    images.wait_until_up('http://127.0.0.1:9/?folder=/x')  # returns as soon as /healthz answers

    def down(url, timeout):
        raise images.urllib.error.URLError('refused')
    monkeypatch.setattr(images.urllib.request, 'urlopen', down)
    monkeypatch.setattr(images.time, 'sleep', lambda s: None)
    with pytest.raises(SystemExit):
        images.wait_until_up('http://127.0.0.1:9/', seconds=0)


def test_an_installed_code_server_runs_on_localhost(monkeypatch, lab, tmp_path):
    started = []

    class Process:
        terminated = False

        def terminate(self):
            Process.terminated = True
    monkeypatch.setattr(images.shutil, 'which', lambda name: '/usr/bin/code-server' if name == 'code-server' else None)
    monkeypatch.setattr(images.subprocess, 'Popen', lambda cmd, **kw: started.append(cmd) or Process())
    monkeypatch.setattr(images, 'wait_until_up', lambda url: None)
    url, stop = images.start_editor(str(lab), str(tmp_path))
    cmd = started[0]
    assert cmd[0] == '/usr/bin/code-server' and cmd[cmd.index('--bind-addr') + 1].startswith('127.0.0.1:')
    assert '--auth' in cmd and cmd[-1] == str(lab) and url.startswith('http://127.0.0.1:')
    stop()
    assert Process.terminated


def test_the_docker_image_runs_when_it_is_here(monkeypatch, lab, tmp_path):
    runs = []

    def run(cmd, **kw):
        runs.append(cmd)
        return types.SimpleNamespace(returncode=0, stdout='', stderr='')
    monkeypatch.setattr(images.shutil, 'which', lambda name: '/usr/bin/docker' if name == 'docker' else None)
    monkeypatch.setattr(images.subprocess, 'run', run)
    monkeypatch.setattr(images, 'wait_until_up', lambda url: None)
    url, stop = images.start_editor(str(lab), str(tmp_path))
    assert runs[0][:3] == ['docker', 'image', 'inspect'] and runs[1][:2] == ['docker', 'run']
    assert url.endswith('/?folder=/home/coder/receitas')
    stop()
    assert runs[-1][:2] == ['docker', 'stop']


def test_docker_that_cannot_start_code_server(monkeypatch, lab, tmp_path):
    answers = iter([0, 1])
    monkeypatch.setattr(images.shutil, 'which', lambda name: '/usr/bin/docker' if name == 'docker' else None)
    monkeypatch.setattr(images.subprocess, 'run', lambda cmd, **kw: types.SimpleNamespace(
        returncode=next(answers), stdout='', stderr='port is already allocated'))
    with pytest.raises(SystemExit):
        images.start_editor(str(lab), str(tmp_path))


def test_a_server_that_never_answers_is_stopped(monkeypatch, lab, tmp_path):
    stopped = []

    class Process:
        def terminate(self):
            stopped.append(True)

    def never(url):
        raise SystemExit(1)
    monkeypatch.setattr(images.shutil, 'which', lambda name: '/usr/bin/code-server' if name == 'code-server' else None)
    monkeypatch.setattr(images.subprocess, 'Popen', lambda cmd, **kw: Process())
    monkeypatch.setattr(images, 'wait_until_up', never)
    with pytest.raises(SystemExit):
        images.start_editor(str(lab), str(tmp_path))
    assert stopped == [True]


def test_drive_editor_opens_files_runs_commands_and_shows_the_view():
    log = []

    class Keyboard:
        def press(self, key):
            log.append(('press', key))

        def type(self, text):
            log.append(('type', text))

    # the real palette lists "Git: Open All Changes" first for "Git: Open Changes": Enter would run the wrong one
    rows = {'Git: Open Changes': ['Git: Open All Changes', 'Git: Open Changes', 'Git: Open Staged Changes']}
    typed_last = lambda: [t for k, t in log if k == 'type'][-1]  # noqa: E731
    page = types.SimpleNamespace(keyboard=Keyboard(), mouse=types.SimpleNamespace(move=lambda x, y: None),
                                 goto=lambda url, **kw: log.append(('goto', url)),
                                 locator=lambda sel: PaletteRows(rows.get(typed_last(), []), log),
                                 wait_for_selector=lambda s, **kw: None, wait_for_timeout=lambda ms: None)
    images.drive_editor(page, 'http://x', ['a.md'], ['Git: Open Changes'], 'scm')
    typed = [t for k, t in log if k == 'type']
    assert typed == ['a.md', 'Git: Open Changes', 'View: Show Source Control', 'Notifications: Clear All Notifications']
    assert log.index(('press', 'Backspace')) < log.index(('type', 'a.md'))  # Quick Open, not a command
    assert ('click', 'Git: Open Changes') in log and ('click', 'Git: Open All Changes') not in log
    after = log[log.index(('type', 'Git: Open Changes')):]
    assert ('press', 'Enter') not in after[:after.index(('click', 'Git: Open Changes'))]


# ---------- images of official documentation repositories on GitHub ----------

def license_file(spdx, text=''):
    return {'license': {'spdx_id': spdx}, 'html_url': 'https://github.com/o/r/blob/main/LICENSE',
            'content': base64.b64encode(text.encode()).decode()}


@pytest.fixture
def github(monkeypatch, commons):
    """Fake GitHub API: one repository with a license, a tree of files; downloads go to the commons fixture."""
    state = {'license': license_file('Apache-2.0'), 'calls': [],
             'tree': ['content/images/virtualization-enabled.png', 'content/images/wsl2-enabled.png',
                      'content/install.md', 'assets/logo.svg']}

    def call(path):
        state['calls'].append(path)
        if path.endswith('/license'):
            return state['license']
        if '/git/trees/' in path:
            return {'tree': [{'path': p, 'type': 'blob'} for p in state['tree']]}
        return {'default_branch': 'main'}
    monkeypatch.setattr(images, 'github_api', call)
    return state, commons


def test_docs_lists_the_images_whose_path_has_the_words(cli, github):
    code, r = cli('images', 'docs', 'docker/docs', 'task manager virtualization')
    assert code == 0 and r['license'] == 'Apache 2.0'
    assert r['images'] == ['github:docker/docs/content/images/virtualization-enabled.png']


def test_docs_refuses_a_repository_without_a_free_license(cli, github):
    state, _ = github
    state['license'] = license_file('NOASSERTION', 'All rights reserved.')
    code, r = cli('images', 'docs', 'acme/docs', 'install')
    assert code == 1 and 'no free license' in r['error']


def test_a_creative_commons_license_github_does_not_name_is_read_from_the_file(cli, github):
    state, _ = github
    state['license'] = license_file('NOASSERTION', 'Attribution 4.0 International\n=====')
    code, r = cli('images', 'docs', 'MicrosoftDocs/WSL', 'wsl')
    assert code == 0 and r['license'] == 'CC BY 4.0'


def test_a_non_commercial_license_is_not_free(cli, github):
    state, _ = github
    state['license'] = license_file('NOASSERTION', 'Attribution-NonCommercial 4.0 International')
    code, r = cli('images', 'docs', 'acme/docs', 'wsl')
    assert code == 1 and 'no free license' in r['error']


def test_fetch_from_github_saves_the_image_and_credits_the_repository(cli, book, github):
    _, commons = github
    code, r = cli('images', 'fetch', 'github:docker/docs/content/images/virtualization-enabled.png',
                  '--name', 'c02-virtualizacao', '--book', book)
    assert code == 0 and (book / 'img' / 'c02-virtualizacao.png').exists()
    assert commons['downloads'] == [
        'https://raw.githubusercontent.com/docker/docs/main/content/images/virtualization-enabled.png']
    credits = (book / 'img' / 'CREDITS.md').read_text(encoding='utf-8')
    assert 'docker/docs contributors' in credits and 'Apache 2.0' in credits
    assert 'https://github.com/docker/docs/blob/main/content/images/virtualization-enabled.png' in credits
    assert r['caption'] == 'docker/docs contributors, Apache 2.0, via GitHub (docker/docs)'


@pytest.mark.parametrize('ref', ['github:docker/docs/content/install.md', 'github:docker/docs/../x.png',
                                 'github:not a repo/x.png'])
def test_fetch_from_github_refuses_what_is_not_an_image_of_the_repository(cli, book, github, ref):
    _, commons = github
    code, r = cli('images', 'fetch', ref, '--name', 'c02-x', '--book', book)
    assert code == 1 and not commons['downloads']
