#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $# -ne 1 ]] || ! [[ "$1" =~ ^[a-f0-9]{40}$ ]]; then echo "Expected full commit SHA" >&2; exit 2; fi
SHA="$1"
cd /opt/erp
test -f deploy/.env
test -s deploy/secrets/db_root_password
test -s deploy/secrets/admin_password
# Refuse to overwrite manual live changes (including local Caddyfile edits).
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Tracked changes exist in /opt/erp; refusing to overwrite live configuration" >&2
  exit 1
fi
git fetch --no-tags origin main
git cat-file -e "$SHA^{commit}"
git merge-base --is-ancestor "$SHA" origin/main || { echo "Commit not on origin/main"; exit 1; }
git checkout --detach "$SHA"
cd deploy
dc=(docker compose -f compose.yaml -f compose.production.yaml -f compose.ssl.yaml -f compose.low-memory.yaml -f compose.registry.yaml)
"${dc[@]}" config --quiet
# Back up the existing site before changing containers. Stop if backup fails.
if "${dc[@]}" ps --status running --services | grep -qx backend; then
  "${dc[@]}" exec -T backend bench --site armember.ir backup --with-files
else
  echo "Backend not running: refusing automated production deployment" >&2
  exit 1
fi
# Never recreate or erase database/volumes from CI.
docker build --build-arg ERPNEXT_VERSION=v16.53.0 -t armember/erpnext:v16.53.0 -f Dockerfile .
"${dc[@]}" up -d --no-deps backend websocket queue-short queue-long scheduler frontend
"${dc[@]}" ps
curl --fail --silent --show-error --retry 12 --retry-delay 5 --retry-connrefused -H 'Host: armember.ir' http://127.0.0.1:8080/ >/dev/null
echo "ERPNext frontend responded successfully."
