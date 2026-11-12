#!/usr/bin/env bash
# Explicit operator-only oil & gas demo seed on the existing ERPNext site.
# This is NOT a deployment hook. It must never run on install/migrate/startup.
# Run manually as root after reviewing the created company and production backup.
set -Eeuo pipefail
umask 077

SITE="armember.ir"
COMPANY="[DEMO] Oil & Gas Operations"
DAYS=365
[[ "${CONFIRM_DEMO_SEED_ON_LIVE_SITE:-}" == "YES" ]] || {
  echo "Refusing: set CONFIRM_DEMO_SEED_ON_LIVE_SITE=YES to acknowledge demo records in a shared live ERP site." >&2
  exit 2
}
[[ "$(id -u)" == 0 ]] || { echo "Run as root through approved server administration." >&2; exit 2; }
cd /opt/erp/deploy
for file in .env compose.yaml compose.production.yaml compose.ssl.yaml compose.low-memory.yaml compose.registry.yaml; do
  [[ -r "$file" ]] || { echo "Missing $file" >&2; exit 2; }
done

# Preserve the current compose project and running application. No Docker up/down.
export COMPOSE_PROJECT_NAME=deploy SITE_NAME="$SITE" HOST_HTTP_PORT=8080
# Existing .env contains image references required for compose config expansion.
set -a
# shellcheck disable=SC1091
source .env
set +a
export COMPOSE_PROJECT_NAME=deploy SITE_NAME="$SITE" HOST_HTTP_PORT=8080
dc=(docker compose -f compose.yaml -f compose.production.yaml -f compose.ssl.yaml -f compose.low-memory.yaml -f compose.registry.yaml)
"${dc[@]}" config --quiet
"${dc[@]}" ps --status running --services | grep -qx backend || { echo "Backend is not running" >&2; exit 3; }
"${dc[@]}" ps --status running --services | grep -qx db || { echo "Database is not running" >&2; exit 3; }
docker inspect deploy-db-1 --format '{{.State.Health.Status}}' | grep -qx healthy || { echo "Database is not healthy" >&2; exit 3; }

# Do not create/modify existing companies, or use the default real company.
# Operators must first provision an independent [DEMO]-prefixed company in ERPNext.
exists="$("${dc[@]}" exec -T backend bench --site "$SITE" execute frappe.db.exists \
  --args '["Company","[DEMO] Oil & Gas Operations"]')"
if [[ "$exists" != *"$COMPANY"* ]]; then
  echo "Missing isolated company '$COMPANY'. No demo records were written." >&2
  echo "Create this separate demo company through ERPNext Setup before running the script." >&2
  exit 3
fi

# Take an independent, fresh, restricted backup of DB, file archives and encryption config.
backup_dir="/var/backups/erpnext/demo-seed-$(date -u +%Y%m%dT%H%M%SZ)"
install -d -m 0700 "$backup_dir"
"${dc[@]}" exec -T backend bench --site "$SITE" backup --with-files
backend_cid="$("${dc[@]}" ps -q backend)"
docker cp "$backend_cid:/home/frappe/frappe-bench/sites/$SITE/private/backups/." "$backup_dir/"
docker cp "$backend_cid:/home/frappe/frappe-bench/sites/$SITE/site_config.json" "$backup_dir/site_config.json"
chmod -R go-rwx "$backup_dir"
find "$backup_dir" -type f -name '*database.sql.gz' -size +0c | grep -q . || {
  echo "No nonempty database backup; refusing seed." >&2; exit 4;
}
find "$backup_dir" -type f -name '*files.tar*' -size +0c | grep -q . || {
  echo "No nonempty files archive; refusing seed." >&2; exit 4;
}
[[ -s "$backup_dir/site_config.json" ]] || { echo "Missing encryption config backup; refusing seed." >&2; exit 4; }
echo "Verified new backup location: $backup_dir"

# Explicitly opt in for the short duration of this single operation only.
cleanup() {
  "${dc[@]}" exec -T backend bench --site "$SITE" set-config enable_oil_gas_demo_seed 0 >/dev/null || true
}
trap cleanup EXIT
"${dc[@]}" exec -T backend bench --site "$SITE" set-config enable_oil_gas_demo_seed 1
"${dc[@]}" exec -T backend bench --site "$SITE" execute bisness_core.demo.seed.seed_demo \
  --kwargs '{"confirm":"SEED_OIL_GAS_DEMO","company":"[DEMO] Oil & Gas Operations","days":365}'
echo "Seed execution returned; inspecting DEMO KPI and Insights records..."
kpi_count="$("${dc[@]}" exec -T backend bench --site "$SITE" execute frappe.db.count \
  --args '["Demo Oil Gas KPI",{"company":"[DEMO] Oil & Gas Operations"}]')"
echo "Demo KPI rows: $kpi_count"
if [[ "$kpi_count" != "4380" ]]; then
  echo "Expected 4,380 demo KPI rows. Please inspect seed output; backup remains at $backup_dir." >&2
  exit 5
fi
dashboard_name="$("${dc[@]}" exec -T backend bench --site "$SITE" execute frappe.db.get_value \
  --args '["Insights Dashboard v3",{"title":"[DEMO] Oil & Gas | Executive Command Center"},"name"]')"
echo "Demo Insights dashboard: $dashboard_name"
if [[ -z "$dashboard_name" || "$dashboard_name" == "None" ]]; then
  echo "Demo KPI rows exist, but Insights dashboard creation did not succeed. Inspect warnings." >&2
  exit 5
fi
echo "Demo KPI count and dashboard are present. Verify all 18 charts in the Insights UI."
echo "Review the printed seeder warnings: any missing CRM or HRMS examples need follow-up."
