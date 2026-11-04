# Generic ERPNext v16 stack — deployment handoff

This repository provides a **customer-independent deployment baseline**, not a live production instance. An operator can use it to create a **new, isolated** ERPNext site. It does not change another Compose project or install apps onto an existing site.

The custom image contains:

1. Frappe + ERPNext v16.53.0, based on `frappe/erpnext:v16.53.0`.
2. Official Frappe HRMS at reviewed tag/commit `v16.53.0` / `b12d935b`.
3. Iranian localization `erpnext_iran` at reviewed commit `60dc7b8b`.
4. Our first-party Frappe package `bisness_core` (the spelling is intentional).

**Scope:** `bisness_core` is an installable extension scaffold. Consolidated accounting, intercompany elimination, treasury workflows, certified tax reporting and complete Iranian HR/payroll compliance are **not** implemented or accepted. Customer RFPs are inputs to a feature backlog, not proof of delivered functionality. Do not load real financial/employee data before security, legal and domain acceptance.

## 1. Operator prerequisites

- A private GitHub access path to the repository, a clean isolated Linux x86_64 host, Docker Engine, Docker Compose v2, `bash`, `openssl` and `curl`.
- For a build host, outbound GitHub and container-registry access and enough CPU/RAM/disk for Frappe asset compilation. Suggested starting capacity for a disposable build: 4 vCPU, 8 GB RAM and 30 GB free disk; actual needs vary.
- A **unique** `COMPOSE_PROJECT_NAME`, an unused `HOST_HTTP_PORT` and a new `SITE_NAME` for each instance. The default `erp-evaluation`, `erp.example.test` and port `18080` are examples, not approved production values.
- A reviewed image tag; record its immutable digest (`docker image inspect`) when promotion is approved. Dockerfile commit checks protect the app sources; Docker base/builder tags are not yet digest-pinned.

Do **not** run this on a busy/shared host without verifying available ports, volume names, ownership, memory and the names of other running Compose projects. The provided private stack does not publish MariaDB or Redis.

## 2. Clone the integration branch and prepare a private instance

Before these changes are merged to `main`, the handoff source is the PR #2 branch:

```bash
git clone --branch feat/generic-erp-bisness-core-20261104 \
  https://github.com/esi-ubuntu/ERP.git
cd ERP/deploy
cp .env.example .env
```

Edit `deploy/.env` locally. Set `COMPOSE_PROJECT_NAME` to a new instance-specific identifier, `SITE_NAME` to the new tenant DNS name, `HOST_HTTP_PORT` to an unused local port, and `CUSTOM_IMAGE`/`CUSTOM_TAG` to a unique build tag. Keep `PULL_POLICY=never` for a locally built image. **Do not commit `.env` or `deploy/secrets/`.** The `upstream/erpnext` Git submodule is reference source only; it is not needed for this Docker build.

## 3. Validate, build and verify the image (no database changes)

```bash
bash scripts/preflight.sh
bash scripts/build-image.sh
```

`preflight.sh` validates required variables and Docker availability. `build-image.sh` builds the custom four-app image and runs `verify-image.sh`. These commands do not start the ERP database, create a site or migrate an existing one. The build **fails closed** when HRMS or Iranian localization no longer matches the reviewed upstream Git commit. Review and explicitly update the pin before retrying; do not bypass it.

The image check verifies the presence and Python imports of the extra apps. It is not evidence that their business processes work.

### Build on a connected workstation; deploy on a restricted server

If the deployment host cannot access Docker Hub or GitHub, build on an authorized connected x86_64 runner. **The target also needs the MariaDB and Redis images** (`mariadb:11.8` and `redis:7-alpine`). Use one of the following controlled transfer paths:

**Private image registry** (requires a deliberate, authorized image push):

```bash
# Build host: tag and push the image to YOUR_CONTROLLED_REGISTRY.
docker tag "erp-platform/erpnext:v16.53.0-apps1" YOUR_CONTROLLED_REGISTRY/erpnext:APPROVED_TAG
docker push YOUR_CONTROLLED_REGISTRY/erpnext:APPROVED_TAG
```

On the deployment host, set `CUSTOM_IMAGE=YOUR_CONTROLLED_REGISTRY/erpnext`, `CUSTOM_TAG=APPROVED_TAG`, `PULL_POLICY=missing`, and `docker pull` the image using configured registry credentials. Do not store a password in Git. If the host has no network path to that registry, use a portable archive:

```bash
# Build host; use the tag from deploy/.env and transfer files securely.
docker save -o erpnext-approved.tar erp-platform/erpnext:v16.53.0-apps1
sha256sum erpnext-approved.tar > erpnext-approved.tar.sha256

# Deployment host: verify the archive received, then load it.
sha256sum -c erpnext-approved.tar.sha256
docker load -i erpnext-approved.tar
```

Keep `PULL_POLICY=never` on a host using `docker load`. Verify the loaded tag matches `CUSTOM_IMAGE:CUSTOM_TAG` in `.env`. Archive/registry transfers are operator actions, not automatic repository side effects. Examples above use the default image tag; replace it with the actual tag.

For a restricted host, also transfer the exact dependency images (after approving their source and platform):

```bash
# Connected host:
docker pull --platform linux/amd64 mariadb:11.8
docker pull --platform linux/amd64 redis:7-alpine
docker save -o erp-dependencies.tar mariadb:11.8 redis:7-alpine
sha256sum erp-dependencies.tar > erp-dependencies.tar.sha256

# Restricted host:
sha256sum -c erp-dependencies.tar.sha256
docker load -i erp-dependencies.tar
```

The optional HTTPS override also needs `caddy:2.10.2-alpine`. Do not assume an offline host can pull any image. Check the actual loaded image tags with `docker image ls` before initialization.

## 4. Initialize one **new** isolated site

Review the environment and Compose configuration before this stateful step:

```bash
bash scripts/preflight.sh
docker compose -f compose.yaml -f compose.production.yaml config --quiet
CONFIRM_INITIALIZE=YES bash scripts/initialize.sh
```

`initialize.sh` requires the image to exist. It checks for an existing or partially created site **before** it starts the database, then generates local secrets, starts MariaDB/Redis/configurator, creates the site, and installs ERPNext, HRMS, Iranian localization and `bisness_core`. It refuses an existing site; it never runs a general upgrade or reset.

This is a **stateful action**. Run it only when the destination is empty and the Compose project is correct. If initialization fails halfway, **stop and inspect** the site and DB state; never blindly rerun or delete volumes.

After the containers settle, run acceptance smoke checks:

```bash
bash scripts/verify-image.sh
bash scripts/smoke-site.sh
```

The smoke test checks that `erpnext`, `hrms`, `erpnext_iran` and `bisness_core` are installed on this site and that the local HTTP ping returns success. It does not validate transactional HRMS or statutory calculations. For a private test site, reach the browser via a trusted SSH tunnel:

```bash
ssh -N -L 18080:127.0.0.1:18080 deploy@YOUR_HOST
```

Use the chosen `HOST_HTTP_PORT` instead of `18080` when changed. The browser URL is then `http://localhost:18080`; read the administrator password privately from `deploy/secrets/admin_password`. Do not print secrets into logs or chat.

## 5. Existing site, upgrades and backups

**Never run `initialize.sh` against a pre-existing site.** For an existing ERPNext installation, the operator must first:

1. Inventory its Frappe/ERPNext versions, installed apps, MariaDB version, image digest and active Compose configuration.
2. Obtain a consistent backup (database, `sites/` files and encryption key) and prove it can be restored in a separate disposable environment.
3. Validate compatibility with the selected ERPNext/HRMS/localization versions; install additional apps in an approved maintenance window with `bench --site SITE install-app APP`, followed by a controlled `bench --site SITE migrate` and smoke checks.
4. Prepare a rollback plan using the original image **and a matching pre-migration backup**. Database schema migration is not generally reversible merely by changing the image tag.

These steps are **not automated** here because the correct plan depends on the source system's live state. Never use `docker compose down -v` or delete existing site/database volumes in a recovery attempt. Copy protected backups off-host, test restore periodically, and enforce retention/encryption.

## 6. Optional public HTTPS

The default HTTP listener is only `127.0.0.1:${HOST_HTTP_PORT}`; it is not public. `compose.ssl.yaml` is **opt-in**. It adds Caddy and publishes `80/tcp`, `443/tcp` and `443/udp`. First confirm that DNS, ACME email, firewall, proxy ownership and those ports are available:

```bash
docker compose -f compose.yaml -f compose.production.yaml -f compose.ssl.yaml config --quiet
```

Only an operator with approved port and DNS ownership should start this override. On a shared host, prefer integration into the existing central reverse proxy. Never expose MariaDB, Redis or the private HTTP backend directly.

## 7. Evidence and release gates

From the repository root, run lightweight static checks:

```bash
python3 -m unittest discover -s tests -v
bash -n deploy/scripts/*.sh
```

The handoff is complete only when a colleague records these **real** results on a disposable deployment: custom image build/digest; Compose config; successful creation; four `list-apps` entries; private HTTP smoke; functional access/permission checks; backup-and-restore rehearsal; and approved Iranian accounting/HR/tax scenarios. See [PRODUCTION.md](PRODUCTION.md) for the remaining release gates.

No Compose `up`, image push, public listener, Git merge or production migration occurs merely by checking out this branch.
