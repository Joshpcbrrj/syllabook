#!/usr/bin/env bash
# Prepares a library with a finished language book: one that teaches English to Portuguese speakers.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="${CLAUDE_PLUGIN_ROOT:-$here/../..}"
mkdir -p created-books
cp -r "$root/tests/fixtures/sample-book" created-books/ingles-do-zero-teste
cp "$root/skills/syllabook/assets/library/library.yaml" library.yaml
python3 - <<'EOF'
import yaml
path = 'created-books/ingles-do-zero-teste/book.yaml'
data = yaml.safe_load(open(path, encoding='utf-8'))
data.update(title='Inglês do zero (exemplo de teste)', slug='ingles-do-zero-teste', profiles=['languages'],
            goal='Apresentar-se e fazer perguntas simples em inglês, no nível A1',
            audience='Brasileiros adultos que nunca estudaram inglês')
yaml.safe_dump(data, open(path, 'w', encoding='utf-8'), allow_unicode=True, sort_keys=False)
EOF
