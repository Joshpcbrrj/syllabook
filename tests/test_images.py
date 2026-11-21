"""images.py: free-license photos from Wikimedia Commons and screenshots of the book's application."""
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

def fake_playwright(monkeypatch, log):
    class Keyboard:
        def press(self, key):
            log.append(('press', key))

        def type(self, text):
            log.append(('type', text))

    class Page:
        keyboard = Keyboard()
        mouse = types.SimpleNamespace(move=lambda x, y: None)

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
