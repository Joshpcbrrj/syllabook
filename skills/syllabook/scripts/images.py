#!/usr/bin/env python3
"""Real images for the book: free-license photos (Wikimedia Commons and Openverse), screenshots of web
pages and of VS Code, each one recorded in img/CREDITS.md (references/SOURCES.md §7).

Usage:
  python scripts/images.py search "<what to look for>" [--limit 6] [--source all|commons|openverse]
  python scripts/images.py fetch "File:<title>" | "openverse:<id>" --name c03-eniac [--book B]
  python scripts/images.py screenshot <url> --name c05-app [--book B] [--width 1280 --height 800]
  python scripts/images.py editor <folder> --name c03-vscode [--open FILE]... [--command "<palette>"]...
                                  [--view explorer|scm|search] [--dark] [--book B] [--width --height]

search lists only public domain, CC0, CC BY and CC BY-SA images, with author, license and the value
to give fetch (--limit is per source). Openverse gathers Flickr, museums and other collections.
fetch downloads the image to img/<name>.<ext>, records the credit and prints the Markdown and the
caption credit to use. A non-free image is refused.
screenshot opens a web page (the book's application, a GitHub page) with Playwright and saves img/<name>.png.
editor opens <folder> in VS Code for the web (code-server, clean settings, no extensions or account),
opens the files, runs the palette commands, shows the view and saves img/<name>.png. It uses code-server
if installed, otherwise the Docker image; it never installs or downloads anything: it says what to ask.
"""
import argparse
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import fail, find_book, out

API = 'https://commons.wikimedia.org/w/api.php'
OPENVERSE = 'https://api.openverse.org/v1/'
OPENVERSE_LICENSES = 'by,by-sa,cc0,pdm'
CODE_SERVER_IMAGE = 'codercom/code-server:4.146.0'
VIEWS = {'explorer': 'View: Show Explorer', 'scm': 'View: Show Source Control', 'search': 'View: Show Search'}
# Wikimedia asks every client to say who it is
AGENT = 'Syllabook/0.3 (https://github.com/Joshpcbrrj/syllabook)'
EXTENSIONS = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif', 'image/webp': '.webp',
              'image/svg+xml': '.svg'}
FREE = re.compile(r'^(public domain|pd\b|pd-|cc0|cc[ -]by( |-sa |-sa$|$)|cc[ -]by[ -]\d|cc[ -]by-sa[ -]\d)', re.I)


def api(params):
    query = urllib.parse.urlencode({**params, 'format': 'json'})
    request = urllib.request.Request(f'{API}?{query}', headers={'User-Agent': AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def openverse_api(path, params=None):
    query = f'?{urllib.parse.urlencode(params)}' if params else ''
    request = urllib.request.Request(f'{OPENVERSE}{path}{query}', headers={'User-Agent': AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def download(url, path):
    request = urllib.request.Request(url, headers={'User-Agent': AGENT})
    with urllib.request.urlopen(request, timeout=60) as response, open(path, 'wb') as f:
        f.write(response.read())


def free_license(name):
    """Public domain, CC0, CC BY or CC BY-SA; NC (non-commercial) and ND (no derivatives) are not free."""
    name = (name or '').strip()
    return bool(FREE.match(name)) and not re.search(r'\b(nc|nd)\b', name, re.I)


def plain(value):
    """Commons metadata comes as HTML: keep the text only."""
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value or ''))).strip()


def describe(page):
    info = (page.get('imageinfo') or [{}])[0]
    meta = info.get('extmetadata') or {}
    value = lambda key: (meta.get(key) or {}).get('value', '')  # noqa: E731
    return {'title': page.get('title'), 'author': plain(value('Artist')) or 'unknown author',
            'license': plain(value('LicenseShortName')), 'license_url': value('LicenseUrl'),
            'source': info.get('descriptionurl'), 'url': info.get('thumburl') or info.get('url'),
            'mime': info.get('mime'), 'size': f'{info.get("width")}x{info.get("height")}',
            'free': free_license(plain(value('LicenseShortName'))) and value('NonFree') != 'true'}


def license_name(code, version):
    """Openverse license codes as people write them: by-sa 2.0 -> CC BY-SA 2.0, pdm -> Public domain."""
    if code == 'pdm':
        return 'Public domain'
    if code == 'cc0':
        return f'CC0 {version}'.strip()
    return f'CC {code.upper()} {version}'.strip()


def describe_openverse(item):
    licence = license_name(item.get('license', ''), item.get('license_version') or '')
    return {'fetch': f'openverse:{item.get("id")}', 'title': item.get('title') or 'untitled',
            'author': item.get('creator') or 'unknown author', 'license': licence,
            'license_url': item.get('license_url') or '', 'source': item.get('foreign_landing_url'),
            'url': item.get('url'), 'size': f'{item.get("width")}x{item.get("height")}',
            'via': f'Openverse ({item.get("source")})',
            'free': free_license(licence) and not item.get('mature')}


INFO = {'prop': 'imageinfo', 'iiprop': 'url|mime|size|extmetadata', 'iiurlwidth': 1280}


def search_commons(query, limit):
    data = api({'action': 'query', 'generator': 'search', 'gsrsearch': query, 'gsrnamespace': 6,
                'gsrlimit': max(limit * 3, 10), **INFO})
    found = [describe(p) for p in (data.get('query') or {}).get('pages', {}).values()]
    for f in found:
        f['fetch'], f['via'] = f['title'], 'Wikimedia Commons'
    return found


def search_openverse(query, limit):
    data = openverse_api('images/', {'q': query, 'license': OPENVERSE_LICENSES, 'page_size': max(limit * 2, 10)})
    return [describe_openverse(i) for i in data.get('results') or []]


def search(query, limit, source):
    results, left_out, unavailable = [], 0, []
    for name, find in (('commons', search_commons), ('openverse', search_openverse)):
        if source not in ('all', name):
            continue
        try:
            found = find(query, limit)
        except (urllib.error.URLError, OSError, ValueError):
            unavailable.append(name)
            continue
        if name == 'openverse' and source == 'all':  # Commons already answered for its own images
            found = [f for f in found if f['via'] != 'Openverse (wikimedia)']
        free = [f for f in found if f.pop('free')]
        left_out += len(found) - len(free)
        results += free[:limit]
    result = {'query': query, 'results': results, 'left_out': left_out,
              'note': 'only public domain, CC0, CC BY and CC BY-SA images; fetch one with images.py fetch <fetch>'}
    if unavailable:
        result['unavailable'] = unavailable
    out(result)


def credit(book_dir, filename, line):
    """Adds the image's line to img/CREDITS.md once."""
    path = os.path.join(book_dir, 'img', 'CREDITS.md')
    text = open(path, encoding='utf-8').read() if os.path.exists(path) else '# Image credits\n'
    if not re.search(rf'^- {re.escape(filename)}:', text, re.M):
        # a blank line between the title and the list, then one line per image
        joiner = '\n' if re.search(r'^- ', text, re.M) else '\n\n'
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text.rstrip('\n') + f'{joiner}- {filename}: {line}\n')


def save_image(book_dir, name, image, extension, title):
    filename = name + extension
    os.makedirs(os.path.join(book_dir, 'img'), exist_ok=True)
    download(image['url'], os.path.join(book_dir, 'img', filename))
    license_text = image['license'] + (f' ({image["license_url"]})' if image['license_url'] else '')
    credit(book_dir, filename, f'{title}, {image["author"]}, {license_text}, {image["source"]}')
    out({'file': f'img/{filename}', 'markdown': f'![<alt text>](../img/{filename})',
         'caption': f'{image["author"]}, {image["license"]}, via {image["via"]}',
         'note': 'write the alt text and put the caption credit under the image'})


def fetch_openverse(ident, name, book_dir):
    try:
        image = describe_openverse(openverse_api(f'images/{ident}/'))
    except urllib.error.HTTPError:
        fail(f'openverse:{ident} not found on Openverse')
    if not image['free']:
        fail(f'openverse:{ident} has no free license ({image["license"] or "none"}): pick another image')
    extension = os.path.splitext(urllib.parse.urlparse(image['url'] or '').path)[1].lower()
    if extension not in EXTENSIONS.values():
        extension = '.jpg'
    save_image(book_dir, name, image, extension, f'"{image["title"]}"')


def fetch(title, name, book_dir):
    if title.startswith('openverse:'):
        return fetch_openverse(title.split(':', 1)[1], name, book_dir)
    pages = list((api({'action': 'query', 'titles': title, **INFO}).get('query') or {}).get('pages', {}).values())
    if not pages or 'missing' in pages[0] or not pages[0].get('imageinfo'):
        fail(f'{title} not found on Wikimedia Commons')
    image = describe(pages[0])
    if not image['free']:
        fail(f'{title} has no free license ({image["license"] or "none"}): pick another image')
    image['via'] = 'Wikimedia Commons'
    save_image(book_dir, name, image, EXTENSIONS.get(image['mime'], '.jpg'), image['title'])


def playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        fail('Playwright is not installed. In Claude Code: ask the user first (it downloads a browser, ~150 MB); '
             'if they agree, pip install playwright && python -m playwright install chromium, otherwise ask them '
             'for the screenshot. On claude.ai (no browser): ask the user for a screenshot of the running application, '
             'save it in img/ and record it in img/CREDITS.md. Never make up a screenshot.')


def screenshot(url, name, book_dir, width, height):
    sync_playwright = playwright()
    os.makedirs(os.path.join(book_dir, 'img'), exist_ok=True)
    filename = f'{name}.png'
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': width, 'height': height})
        page.goto(url, wait_until='networkidle')
        page.screenshot(path=os.path.join(book_dir, 'img', filename), full_page=False)
        browser.close()
    credit(book_dir, filename, f'screenshot of the book\'s application running at {url}, taken while writing the book')
    out({'file': f'img/{filename}', 'markdown': f'![<alt text>](../img/{filename})'})


def write_settings(user_data, dark):
    """Clean, readable VS Code settings: default theme, no telemetry, tips, trust prompts or AI panels."""
    os.makedirs(os.path.join(user_data, 'User'), exist_ok=True)
    settings = {
        'workbench.colorTheme': 'Default Dark Modern' if dark else 'Default Light Modern',
        'workbench.startupEditor': 'none', 'workbench.tips.enabled': False,
        'workbench.welcomePage.walkthroughs.openOnInstall': False,
        'telemetry.telemetryLevel': 'off', 'security.workspace.trust.enabled': False,
        'extensions.ignoreRecommendations': True, 'update.mode': 'none', 'chat.disableAIFeatures': True,
        'git.openRepositoryInParentFolders': 'always', 'git.autofetch': False,
        'workbench.secondarySideBar.defaultVisibility': 'hidden',
        'editor.fontSize': 15, 'editor.minimap.enabled': False,
    }
    with open(os.path.join(user_data, 'User', 'settings.json'), 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


SERVER_FLAGS = ['--auth', 'none', '--disable-telemetry', '--disable-update-check', '--disable-workspace-trust',
                '--disable-getting-started-override']


def docker_server(folder, port, user_data):
    """The docker run command and URL: bound to 127.0.0.1 only, the folder mounted read-only."""
    inside = f'/home/coder/{os.path.basename(os.path.normpath(folder))}'
    cmd = ['docker', 'run', '--rm', '-d', '--name', f'syllabook-editor-{port}', '-p', f'127.0.0.1:{port}:8080',
           # the mounted folder belongs to another user: let git read it
           '-e', 'GIT_CONFIG_COUNT=1', '-e', 'GIT_CONFIG_KEY_0=safe.directory', '-e', 'GIT_CONFIG_VALUE_0=*',
           '-v', f'{folder}:{inside}:ro', '-v', f'{user_data}:/home/coder/ud',
           CODE_SERVER_IMAGE, '--bind-addr', '0.0.0.0:8080', '--user-data-dir', '/home/coder/ud',
           *SERVER_FLAGS, inside]
    return cmd, f'http://127.0.0.1:{port}/?folder={inside}'


def wait_until_up(url, seconds=90):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url.split('?')[0] + 'healthz', timeout=5):
                return
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    fail(f'code-server did not start in {seconds} s')


def start_editor(folder, user_data):
    """Starts code-server (installed, or the Docker image) and returns (url, stop)."""
    port = free_port()
    native = shutil.which('code-server')
    if native:
        process = subprocess.Popen([native, '--bind-addr', f'127.0.0.1:{port}', '--user-data-dir', user_data,
                                    '--extensions-dir', os.path.join(user_data, 'extensions'), *SERVER_FLAGS,
                                    folder], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f'http://127.0.0.1:{port}/?folder={urllib.parse.quote(folder)}'
        stop = process.terminate
    elif shutil.which('docker'):
        if subprocess.run(['docker', 'image', 'inspect', CODE_SERVER_IMAGE], capture_output=True).returncode:
            fail(f'the code-server image is not here. ask the user first (it downloads about 380 MB, once); if they '
                 f'agree: docker pull {CODE_SERVER_IMAGE}. Otherwise ask them for the screenshot.')
        if os.name != 'nt':
            os.chmod(user_data, 0o777)  # the container runs as another user
        cmd, url = docker_server(folder, port, user_data)
        started = subprocess.run(cmd, capture_output=True, text=True)
        if started.returncode:
            fail(f'docker could not start code-server: {started.stderr.strip()[-300:]}')
        stop = lambda: subprocess.run(['docker', 'stop', f'syllabook-editor-{port}'], capture_output=True)  # noqa: E731
    else:
        fail('neither code-server nor Docker is installed. ask the user: install Docker (then docker pull '
             f'{CODE_SERVER_IMAGE}) or code-server (https://coder.com/docs/code-server/install), or ask them for '
             'the screenshot, saying exactly what to open and the file name.')
    try:
        wait_until_up(url)
    except SystemExit:
        stop()
        raise
    return url, stop


def palette(page, text, quick_open=False):
    """Runs a command (or opens a file) through VS Code's command palette."""
    page.keyboard.press('F1')
    page.wait_for_timeout(400)
    if quick_open:
        page.keyboard.press('Backspace')  # drop the ">" prefix: the palette becomes Quick Open
    page.keyboard.type(text)
    page.wait_for_timeout(800)
    page.keyboard.press('Enter')
    page.wait_for_timeout(1200)


def drive_editor(page, url, files, commands, view):
    page.goto(url, wait_until='domcontentloaded')
    page.wait_for_selector('.monaco-workbench', timeout=90000)
    page.wait_for_timeout(4000)  # extensions (git) finish loading
    for file in files:
        palette(page, file, quick_open=True)
    for command in commands:
        palette(page, command)
    if view:
        palette(page, VIEWS[view])
    palette(page, 'Notifications: Clear All Notifications')
    page.mouse.move(0, 0)
    page.wait_for_timeout(1500)


def editor(folder, name, book_dir, files, commands, view, dark, width, height):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        fail(f'folder not found: {folder}')
    sync_playwright = playwright()
    os.makedirs(os.path.join(book_dir, 'img'), exist_ok=True)
    filename = f'{name}.png'
    with tempfile.TemporaryDirectory(prefix='syllabook-editor-') as user_data:
        write_settings(user_data, dark)
        url, stop = start_editor(folder, user_data)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={'width': width, 'height': height})
                drive_editor(page, url, files, commands, view)
                page.screenshot(path=os.path.join(book_dir, 'img', filename), full_page=False)
                browser.close()
        finally:
            stop()
    version = CODE_SERVER_IMAGE.split(':')[-1]
    credit(book_dir, filename, f'screenshot of VS Code (code-server {version}, default settings) with the '
                               f'folder {os.path.basename(folder)}, taken while writing the book')
    out({'file': f'img/{filename}', 'markdown': f'![<alt text>](../img/{filename})',
         'caption': 'VS Code (code-server)',
         'note': 'look at the image before using it; write the alt text and the caption'})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--limit', type=int, default=6)
    s.add_argument('--source', choices=['all', 'commons', 'openverse'], default='all')
    f = sub.add_parser('fetch')
    f.add_argument('title')
    f.add_argument('--name', required=True)
    f.add_argument('--book')
    c = sub.add_parser('screenshot')
    c.add_argument('url')
    c.add_argument('--name', required=True)
    c.add_argument('--book')
    c.add_argument('--width', type=int, default=1280)
    c.add_argument('--height', type=int, default=800)
    e = sub.add_parser('editor')
    e.add_argument('folder')
    e.add_argument('--name', required=True)
    e.add_argument('--open', action='append', default=[], dest='files')
    e.add_argument('--command', action='append', default=[], dest='commands')
    e.add_argument('--view', choices=sorted(VIEWS))
    e.add_argument('--dark', action='store_true')
    e.add_argument('--book')
    e.add_argument('--width', type=int, default=1280)
    e.add_argument('--height', type=int, default=800)
    args = p.parse_args()
    if args.cmd == 'search':
        search(args.query, args.limit, args.source)
    book_dir, _ = find_book(args.book)
    if args.cmd == 'fetch':
        fetch(args.title, args.name, book_dir)
    if args.cmd == 'editor':
        editor(args.folder, args.name, book_dir, args.files, args.commands, args.view, args.dark,
               args.width, args.height)
    screenshot(args.url, args.name, book_dir, args.width, args.height)


if __name__ == '__main__':
    main()
