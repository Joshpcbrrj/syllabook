#!/usr/bin/env bash
# Prepares a library with a finished book (the sample book of the tests), ready to translate or publish.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="${CLAUDE_PLUGIN_ROOT:-$here/../..}"
mkdir -p created-books
cp -r "$root/tests/fixtures/sample-book" created-books/python-do-zero-teste
cp "$root/skills/syllabook/assets/library/library.yaml" library.yaml
