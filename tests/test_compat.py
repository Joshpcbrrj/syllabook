"""The 1.x promise: a book.yaml or library.yaml written by an earlier version stays valid.

The fixtures in tests/fixtures/compat/ are real files as they were saved: the sample book and the library
skeleton of 0.4.0, and the book.yaml of a book published with 0.4.1. Never update them to make a test pass:
a change that breaks one of them is a breaking change (CHANGELOG, and only in a major version).
"""
import os
import shutil

import pytest
from conftest import SAMPLE

COMPAT = os.path.join(os.path.dirname(__file__), 'fixtures', 'compat')


@pytest.mark.parametrize('name', ['book-0.4.0-sample.yaml', 'book-0.4.1-wsl-do-zero.yaml'])
def test_an_older_book_yaml_is_still_valid(cli, tmp_path, name):
    path = tmp_path / 'book.yaml'
    shutil.copy(os.path.join(COMPAT, name), path)
    code, r = cli('book', 'validate', path)
    assert code == 0 and r['ok'] and not r['errors'], r


def test_an_older_library_yaml_still_builds_the_lists(cli, tmp_path):
    lib = tmp_path / 'lib'
    shutil.copytree(SAMPLE, lib / 'created-books' / 'python-do-zero-teste')
    shutil.copy(os.path.join(COMPAT, 'library-0.4.0.yaml'), lib / 'library.yaml')
    code, r = cli('build', 'lists', '--library', lib)
    assert code == 0 and r['books'] == 1, r
