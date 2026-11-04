#!/usr/bin/env bash
set -euo pipefail

# Project-scoped and isolated. Never operate on the ERP Docker stack.
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 is required.' >&2
  exit 1
fi
if [[ ! -x .graphify-venv/bin/graphify ]]; then
  python3 -m venv .graphify-venv
fi
.graphify-venv/bin/python -m pip install --disable-pip-version-check -r .graphify/requirements.txt

# Install the generic agent integration into this repository only.
.graphify-venv/bin/graphify install --platform agents --project

# Process code/config locally; do not use an external model for documents/media.
export GRAPHIFY_BACKEND=none
export GRAPHIFY_QUERY_LOG_DISABLE=1
.graphify-venv/bin/graphify extract . --code-only --out . --force
.graphify-venv/bin/graphify cluster-only .
.graphify-venv/bin/graphify export html

test -s graphify-out/graph.json
test -s graphify-out/GRAPH_REPORT.md
test -s graphify-out/graph.html
echo 'Graphify outputs verified under graphify-out/.'
