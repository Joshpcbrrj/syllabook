#!/usr/bin/env bash
# A finished book as the user gets it from a zip the skill delivered: a folder with book.yaml, no library.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="${CLAUDE_PLUGIN_ROOT:-$here/../..}"
mkdir -p livro-pronto
cp -r "$root/tests/fixtures/sample-book" livro-pronto/python-do-zero-teste
