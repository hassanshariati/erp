#!/usr/bin/env bash
# Inspect the locally built image; never connect to any database.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
test -f .env || { echo "Missing deploy/.env."; exit 2; }
set -a
source ./.env
set +a
: "${CUSTOM_IMAGE:?}"
: "${CUSTOM_TAG:?}"

IMAGE="${CUSTOM_IMAGE}:${CUSTOM_TAG}"
docker image inspect "$IMAGE" >/dev/null
docker run --rm --entrypoint bash "$IMAGE" -lc '
  set -Eeuo pipefail
  cd /home/frappe/frappe-bench
  for app in frappe erpnext hrms erpnext_iran bisness_core crm insights wiki; do
    test -d "apps/$app" || { echo "Missing app: $app"; exit 1; }
  done
  ./env/bin/python -m pip show hrms erpnext_iran bisness_core crm insights wiki >/dev/null
  test -s assets/bisness_core/css/login-theme.css || { echo "Missing packaged login CSS"; exit 1; }
  test -s assets/bisness_core/images/login-visual.svg || { echo "Missing packaged login illustration"; exit 1; }
  test -d assets/wiki/frontend/assets || { echo "Wiki frontend asset directory missing"; exit 1; }
  find assets/wiki/frontend/assets -maxdepth 1 -type f -name "index-*.js" -size +0c -print -quit | grep -q . || { echo "Wiki JavaScript bundle missing"; exit 1; }
  find assets/wiki/frontend/assets -maxdepth 1 -type f -name "index-*.css" -size +0c -print -quit | grep -q . || { echo "Wiki CSS bundle missing"; exit 1; }
  echo "Wiki frontend and full app image package checks passed."
'
