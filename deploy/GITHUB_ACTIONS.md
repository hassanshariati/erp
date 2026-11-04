# GitHub Actions deployment for armember.ir

## Pipeline

`.github/workflows/build-staging.yml` is the supported four-app release path. A GitHub-hosted Ubuntu runner builds the pinned ERPNext v16 image containing HRMS, Iranian localization and `bisness_core`. It initializes a disposable MariaDB-backed site, checks the four installed apps and private HTTP, then publishes the image as `ghcr.io/hassanshariati/erp:apps-<full-commit-sha>`.

The `production` job runs on the dedicated `erpnext-deploy` self-hosted runner. It uses a fixed root-owned deployment executable to pull the approved image and, after an on-host backup, install apps and migrate the pre-existing `armember.ir` site. An unsuccessful build cannot advance to production.

**The older `.github/workflows/deploy.yml` and `deploy/scripts/ci-deploy.sh` are intentionally blocked for the multi-app Dockerfile. Do not remove their safety check to publish this release.**

## One-time host bootstrap (root)

First make the repository private, protect the `main` branch, and configure required reviewers for the `production` environment where supported. A public repository combined with a production-capable self-hosted runner is a meaningful security risk.

On the original VPS, review `deploy/scripts/upgrade-existing-production.sh`, then run:

```bash
cd /opt/erp
git pull --ff-only origin main
sudo bash deploy/scripts/bootstrap-gha-release.sh
```

The bootstrap copies the reviewed script to `/usr/local/sbin/erpnext-gha-release` as root:root (0755), creates a narrowly scoped sudoers command for `gha-erp`, verifies sudoers syntax, and creates `/var/backups/erpnext` with root-only permissions.

**Do not put `gha-erp` in the Docker group, make `/opt/erp/deploy/.env` world-readable, or copy database secrets to the GitHub Actions workspace.** The runner must not have general root or Docker daemon access. The privileged wrapper accepts only a GHCR image tag in the expected owner/repository/40-digit-SHA format.

After a successful hosted build and publication, the `production` job is expected to fail at its permission preflight until the bootstrap is complete. Once installed, rerun the failed production job from GitHub Actions.

## Production upgrade safeguards

The pinned root-owned wrapper uses the existing Docker Compose project name `deploy`, site `armember.ir`, and localhost HTTP port 8080. It never runs `bench new-site`, `docker compose down -v` or deletes named volumes. It verifies database/container status, runs `bench backup --with-files`, and saves the database backup, file archives and original site configuration/encryption key under `/var/backups/erpnext` outside Docker volumes before any schema changes.

During the maintenance window, it pauses queues, updates the site apps list, installs `hrms`, `erpnext_iran` and `bisness_core` if absent, runs `bench migrate`, recreates only Frappe application containers, enables the scheduler, turns off maintenance mode, and verifies private/public HTTP.

**Important:** Successful fresh-site CI tests do not prove successful migration or restore of your production dataset. Before any live schema migration, test restoration with a copy of real backup on an isolated instance, agree on a rollback plan and ensure offsite/encrypted backups. On migration failure, the script deliberately stops rather than attempting an unverified automatic rollback. Merely reverting the Docker image does not undo database changes.

## Troubleshooting

If production shows `One-time server bootstrap required`, install the host wrapper above. If the hosted build or installation fails, read the GitHub Actions job logs; nothing on the VPS was changed. If the production wrapper reports a database or backup error, it stops before applying migrations. If a failure occurs during migration, preserve logs and backups and investigate before retrying.
