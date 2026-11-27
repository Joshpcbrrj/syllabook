"""The repository as a whole: the skill's structure, the documentation and the library skeleton."""
import filecmp
import glob
import os
import re

import pytest
import yaml
from conftest import ROOT, SKILL, read

# scripts cited by the skill but still being written (phase 3 of the rebuild);
# remove each name as soon as its script lands
PENDING_SCRIPTS = set()


def skill_docs():
    return [os.path.join(SKILL, 'SKILL.md')] + sorted(
        glob.glob(os.path.join(SKILL, 'modes', '*.md'))
        + glob.glob(os.path.join(SKILL, 'references', '**', '*.md'), recursive=True))


def rel(path, base=SKILL):
    return os.path.relpath(path, base).replace(os.sep, '/')


def test_skill_frontmatter_follows_the_agent_skills_rules():
    text = read(os.path.join(SKILL, 'SKILL.md'))
    m = re.match(r'---\n(.+?)\n---\n', text, re.S)
    assert m, 'frontmatter not found'
    # parsed as YAML, like the validators do: an unquoted ": " inside the description breaks it
    front = yaml.safe_load(m.group(1))
    assert isinstance(front, dict) and set(front) <= {'name', 'description', 'license', 'compatibility',
                                                     'metadata', 'allowed-tools'}, front
    name, desc = front['name'], front['description']
    assert name == os.path.basename(SKILL)
    assert re.fullmatch(r'[a-z0-9-]{1,64}', name) and not re.search(r'anthropic|claude', name)
    assert 0 < len(desc) <= 1024 and not re.search(r'<[a-zA-Z/]', desc)
    assert len(text.splitlines()) <= 500


def test_every_path_cited_in_the_skill_exists():
    missing = []
    for path in skill_docs():
        text = read(path)
        for ref in set(re.findall(r'`((?:modes|references|assets)/[\w./-]+)`', text)):
            if not os.path.exists(os.path.join(SKILL, ref)):
                missing.append(f'{rel(path)} -> {ref}')
        for ref in set(re.findall(r'scripts/([\w-]+\.py)', text)) - PENDING_SCRIPTS:
            if not os.path.exists(os.path.join(SKILL, 'scripts', ref)):
                missing.append(f'{rel(path)} -> scripts/{ref}')
    assert not missing


def test_every_script_is_taught_somewhere_in_the_skill():
    """SKILL.md lists only the everyday scripts; each of the others must be taught in a mode or reference."""
    text = '\n'.join(read(path) for path in skill_docs())
    # imported by the scripts, not commands; diagram_*.py are the parts of diagram.py
    modules = {'common.py', 'icons.py', 'diagram_draw.py', 'diagram_layouts.py', 'diagram_music.py'}
    scripts = {n for n in os.listdir(os.path.join(SKILL, 'scripts')) if n.endswith('.py')} - modules
    untaught = sorted(n for n in scripts if f'scripts/{n}' not in text and f'`{n}' not in text)
    assert not untaught


def test_every_script_command_and_option_in_the_instructions_exists():
    """An instruction must never send Claude to a command or option the script does not have."""
    scripts = {os.path.basename(p): read(p) for p in glob.glob(os.path.join(SKILL, 'scripts', '*.py'))}
    problems = set()
    for doc in skill_docs():
        for m in re.finditer(r'`(?:python )?(?:scripts/)?([a-z]+\.py)((?: [^`\n]*)?)`', read(doc)):
            script, rest = m.group(1), m.group(2)
            if script not in scripts:
                problems.add(f'{rel(doc)}: unknown script {script}')
                continue
            for flag in set(re.findall(r'(--[a-z][a-z-]*)', rest)) - {'--help'}:
                if f"'{flag}'" not in scripts[script]:
                    problems.add(f'{rel(doc)}: {script} has no option {flag}')
            words = rest.split()
            if script in ('book.py', 'images.py', 'build.py') and words and re.fullmatch(r'[a-z]+', words[0]):
                if f"'{words[0]}'" not in scripts[script]:
                    problems.add(f'{rel(doc)}: {script} has no command {words[0]}')
    assert not problems, sorted(problems)


def test_pending_scripts_list_is_up_to_date():
    landed = PENDING_SCRIPTS & set(os.listdir(os.path.join(SKILL, 'scripts')))
    assert not landed, f'remove from PENDING_SCRIPTS: {sorted(landed)}'


def test_every_mode_and_reference_is_listed_in_skill_md():
    skill = read(os.path.join(SKILL, 'SKILL.md'))
    unlisted = []
    for path in skill_docs()[1:]:
        r = rel(path)
        folder, name = os.path.split(r)
        if r not in skill and name not in skill and f'{folder}/<' not in skill:
            unlisted.append(r)
    assert not unlisted


def test_long_skill_files_start_with_a_table_of_contents():
    for path in skill_docs()[1:]:
        lines = read(path).splitlines()
        head = '\n'.join(lines[:12])
        assert len(lines) <= 100 or '## Contents' in head or '- [ ] 1.' in head, rel(path)


def test_hidden_answers_in_the_skill_use_the_exact_details_format():
    bad = []
    for path in skill_docs():
        lines = read(path).splitlines()
        for i, line in enumerate(lines):
            bare = line.lstrip('> ').strip()
            if bare.startswith('<summary>') and i + 1 < len(lines) and lines[i + 1].lstrip('> ').strip():
                bad.append(f'{rel(path)}:{i + 2}')
            if bare == '</details>' and i > 0 and lines[i - 1].lstrip('> ').strip():
                bad.append(f'{rel(path)}:{i}')
    assert not bad


def test_every_documentation_page_has_the_language_switcher():
    import translation
    missing = [page for r in translation.english_pages() for page in (r, translation.translation_of(r))
               if os.path.exists(os.path.join(ROOT, page)) and 'English' not in read(os.path.join(ROOT, page))[:600]]
    assert not missing


def test_internal_links_point_to_existing_files():
    broken = []
    for path in glob.glob(os.path.join(ROOT, '**', '*.md'), recursive=True):
        r = rel(path, ROOT)
        if r.startswith(('plano/', 'skills/syllabook/references/')):
            continue
        for target in re.findall(r'\]\(([^)#\s]+)(?:#[^)]*)?\)', read(path)):
            if target.startswith(('http://', 'https://', 'mailto:', '../../')):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), target))):
                broken.append(f'{r} -> {target}')
    assert not broken


@pytest.mark.parametrize('relpath', ['LICENSE', 'LICENSE-CODIGO'])
def test_root_licenses_match_the_library_skeleton(relpath):
    copy = os.path.join(SKILL, 'assets', 'library', relpath)
    assert filecmp.cmp(os.path.join(ROOT, relpath), copy, shallow=False), f'{relpath} differs from assets/library'


def test_the_kit_repository_holds_no_library_folders():
    # books live in each user's own library (the syllabook-library template), never here
    leftovers = ['created-books', 'improved-materials', 'site', 'library.yaml',
                 '.github/workflows/epub.yml', '.github/workflows/site.yml']
    assert not [p for p in leftovers if os.path.exists(os.path.join(ROOT, p))]


def test_yaml_files_are_valid_and_library_yaml_has_every_key():
    keys = {'author', 'repository', 'branch', 'commit_name', 'commit_email', 'default_language',
            'content_license', 'code_license', 'epub_release', 'notion_page'}
    files = glob.glob(os.path.join(ROOT, '.github', '**', '*.yml'), recursive=True)
    files += glob.glob(os.path.join(SKILL, 'assets', '**', '*.yml'), recursive=True)
    for path in files:
        yaml.safe_load(read(path))
    assert keys <= set(yaml.safe_load(read(os.path.join(SKILL, 'assets', 'library', 'library.yaml'))))


def test_workflows_that_publish_run_only_in_the_kit_repository():
    for name in ('tests.yml', 'skill-release.yml'):
        assert "github.repository == 'Joshpcbrrj/syllabook'" in read(os.path.join(ROOT, '.github', 'workflows', name))


TEXT_FILES = ('.py', '.md', '.yaml', '.yml', '.json', '.toml', '.txt', '.svg', '.sh', '.ps1', '.html', '.css')
CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def test_text_files_have_no_control_characters():
    # a stray backspace once turned "\b" in a regex into an invisible character; only tests caught it
    import subprocess
    files = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    found = []
    for rel_path in files:
        if rel_path.endswith(TEXT_FILES) and os.path.exists(os.path.join(ROOT, rel_path)):
            text = open(os.path.join(ROOT, rel_path), encoding='utf-8', errors='replace').read()
            for n, line in enumerate(text.splitlines(), 1):
                if CONTROL.search(line.replace('\t', ' ')):
                    found.append(f'{rel_path}:{n}')
    assert not found, found


def test_the_pre_commit_hook_runs_the_lint():
    hook = os.path.join(ROOT, '.githooks', 'pre-commit')
    assert os.path.exists(hook) and 'ruff check' in read(hook)
    assert 'core.hooksPath .githooks' in read(os.path.join(ROOT, 'CONTRIBUTING.md'))
    assert 'core.hooksPath .githooks' in read(os.path.join(ROOT, 'CONTRIBUTING.pt-BR.md'))


def test_images_does_not_hard_code_a_version():
    import importlib
    images = importlib.import_module('images')
    assert not re.search(r'/\d', images.AGENT), images.AGENT
