#!/usr/bin/env bash
# Runs `claude plugin eval` in WSL with a temporary HOME. Docker Desktop's WSL integration turns
# ~/.docker/contexts into a link to Windows, and the eval then refuses every case that grants Bash;
# a HOME without ~/.docker, linking only Claude Code's own files, lets those cases run.
# Usage (from Windows): wsl -e bash -lc "'/mnt/d/<repo>/evals/wsl-eval.sh' --case 14-publicar-livro-pronto ..."
set -euo pipefail
real="$HOME"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for item in .claude .claude.json .local; do
  [ -e "$real/$item" ] && ln -s "$real/$item" "$tmp/$item"
done
cd "$(dirname "$(readlink -f "$0")")/.."
HOME="$tmp" PATH="$real/.local/bin:$PATH" claude plugin eval . "$@"
