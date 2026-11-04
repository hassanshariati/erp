#!/usr/bin/env bash
# Existing-site upgrade: no new-site creation, no removal of Docker volumes.
set -Eeuo pipefail

if [[ $# -ne 1 ]] || ! [[ "$1" =~ ^ghcr[.]io/hassanshariati/erp:apps-[a-f0-9]{40}$ ]]; then
  echo "Usage: $0 ghcr.io/hassanshariati/erp:apps-FULL_COMMIT_SHA" >&2
  exit 2
fi
source_image="$1"
sha="${source_image##*apps-}"
local_image="armember/erpnext:v16.53.0-apps-${sha:0:12}"

[[ "$(id -u)" -eq 0 ]] || { echo "Only the root-owned restricted deployment wrapper may deploy." >&2; exit 1; }
if [[ ! -r /dev/stdin ]]; then
  echo "Missing GitHub Container Registry authentication token." >&2; exit 1
fi
IFS= read -r ghcr_token || { echo "Cannot read GHCR authentication token." >&2; exit 1; }
[[ -n "$ghcr_token" ]] || { echo "Empty GHCR authentication token." >&2; exit 1; }
printf '%s\n' "$ghcr_token" | docker login ghcr.io -u hassanshariati --password-stdin >/dev/null
unset ghcr_token
trap 'docker logout ghcr.io >/dev/null 2>&1 || true' EXIT
cd /opt/erp/deploy
for file in .env compose.yaml compose.production.yaml compose.ssl.yaml compose.low-memory.yaml compose.registry.yaml secrets/db_root_password; do
  test -r "$file" || { echo "Cannot read $file" >&2; exit 1; }
done
docker info >/dev/null

# Preserve existing Compose project, named volumes, and current localhost port.
export COMPOSE_PROJECT_NAME=deploy
export SITE_NAME=armember.ir
export HOST_HTTP_PORT=8080
export CUSTOM_IMAGE=armember/erpnext
export CUSTOM_TAG="${local_image##*:}"
export PULL_POLICY=never
# Older compose.ssl.yaml selects image via ERPNEXT_VERSION; newer via CUSTOM_TAG.
export ERPNEXT_VERSION="$CUSTOM_TAG"
dc=(docker compose -f compose.yaml -f compose.production.yaml -f compose.ssl.yaml -f compose.low-memory.yaml -f compose.registry.yaml)
"${dc[@]}" config --quiet

for service in backend db; do
  "${dc[@]}" ps --status running --services | grep -qx "$service" || {
    echo "Existing $service is not running; refusing live upgrade." >&2; exit 1;
  }
done
docker inspect deploy-db-1 --format '{{.State.Health.Status}}' | grep -qx healthy || {
  echo "MariaDB is not healthy." >&2; exit 1;
}
# Verify app-to-DB authentication before any migration or site change.
"${dc[@]}" exec -T backend bench --site armember.ir list-apps
curl --fail --silent --show-error --max-time 15 -H 'Host: armember.ir' \
  http://127.0.0.1:8080/api/method/ping >/dev/null

echo "Pulling approved image $source_image"
docker pull "$source_image"
docker tag "$source_image" "$local_image"
docker run --rm --network none --entrypoint bash "$local_image" -lc \
  'cd /home/frappe/frappe-bench && for app in frappe erpnext hrms erpnext_iran bisness_core crm insights; do test -d "apps/$app"; done'

# Back up database/files and encryption configuration outside the Docker volumes.
# Never upload production backups to Actions artifacts.
backup_dir="/var/backups/erpnext/$(date -u +%Y%m%dT%H%M%SZ)-${sha:0:12}"
install -d -m 700 "$backup_dir"
"${dc[@]}" exec -T backend bench --site armember.ir backup --with-files
backend_cid="$("${dc[@]}" ps -q backend)"
docker cp "$backend_cid:/home/frappe/frappe-bench/sites/armember.ir/private/backups/." "$backup_dir/"
docker cp "$backend_cid:/home/frappe/frappe-bench/sites/armember.ir/site_config.json" "$backup_dir/site_config.json"
chmod -R go-rwx "$backup_dir"
find "$backup_dir" -type f -name '*database.sql.gz' -size +0c | grep -q . || {
  echo "Database backup not verified; aborting before modifying the site." >&2; exit 1;
}
test -s "$backup_dir/site_config.json" || {
  echo "Site configuration/encryption backup missing." >&2; exit 1;
}
echo "Backup saved securely: $backup_dir"

# The following changes site schema. Failure requires operator-led restoration
# from the matching backup; switching only the Docker image is not a rollback.
"${dc[@]}" exec -T backend bench --site armember.ir set-maintenance-mode on
"${dc[@]}" stop scheduler queue-short queue-long

"${dc[@]}" run --rm --no-deps backend bash -lc '
  set -Eeuo pipefail
  ls -1 apps > sites/apps.txt
  for app in hrms erpnext_iran bisness_core crm insights; do
    if bench --site armember.ir list-apps | awk "{print \$1}" | grep -qx "$app"; then
      echo "$app already installed"
    else
      bench --site armember.ir install-app "$app"
    fi
  done
  bench --site armember.ir migrate
'
"${dc[@]}" up -d --no-deps backend frontend websocket queue-short queue-long scheduler
"${dc[@]}" exec -T backend bench --site armember.ir enable-scheduler
"${dc[@]}" exec -T backend bench --site armember.ir set-maintenance-mode off
installed="$("${dc[@]}" exec -T backend bench --site armember.ir list-apps)"
printf '%s\n' "$installed"
for app in erpnext hrms erpnext_iran bisness_core crm insights; do
  printf '%s\n' "$installed" | grep -Eq "^$app([[:space:]]|$)" || {
    echo "Missing expected installed app: $app" >&2; exit 1;
  }
done
curl --fail --silent --show-error --retry 12 --retry-delay 5 --retry-connrefused \
  -H 'Host: armember.ir' http://127.0.0.1:8080/api/method/ping >/dev/null
curl --fail --silent --show-error --retry 6 --retry-delay 5 \
  https://armember.ir/api/method/ping >/dev/null
# Both standalone SPA pages must resolve on the existing site, not new tenants.
for path in crm insights; do
  code="$(curl --silent --show-error --retry 8 --retry-delay 5 \
    --output /dev/null --write-out '%{http_code}' "https://armember.ir/$path")"
  echo "/$path guest HTTP $code"
  case "$code" in
    200|301|302|303|401|403) ;;
    *) echo "Unexpected response from /$path: $code" >&2; exit 1 ;;
  esac
done
echo "Six-app ERPNext upgrade (including CRM and Insights) completed and verified."
