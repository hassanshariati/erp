# ERP — reusable business platform

A customer-independent commercial ERP product under development, based on **ERPNext v16.53.0**, official **Frappe HRMS v16**, an evaluated **Iranian localization** app, and our first-party Frappe extension **`bisness_core`**. The visible product component name follows the requested spelling `bisness-core`, while Python/Frappe imports use `bisness_core`.

**Product boundary:** Never encode a customer, legal entity, domain, national identifier, tax account, hardcoded company hierarchy or statutory rate in the application source. Companies/sites/roles and legal settings are data and configuration. This is the foundation for selling the same product to multiple unrelated organizations.

## Architecture and status

- [Product architecture and licensing decisions](docs/architecture/product-core.md) and [machine-readable product graph](docs/architecture/product-components.json)
- [Installable Frappe application](apps/bisness_core/README.md): first version is a clean scaffold with no customer-specific business behavior.
- [Private build and first-site deployment guide](deploy/README.md): custom ERPNext image with HRMS and Iranian app, with no automatic live deployment.
- [Deployment safety gate](deploy/PRODUCTION.md).
- [Customer requirement records](docs/requirements/README.md) and [requirement graph](docs/architecture/requirements-graph.md): specific customer material is **not** a universal product requirement or preconfigured company data.
- [Graphify scope and instructions](.graphify/README.md): run manually; code graph is not runtime proof.

## Clone and static checks

While the deployment code is under review in Draft PR #2, use its integration branch. The ERPNext submodule is not required for the Docker build:

```bash
git clone --branch feat/generic-erp-bisness-core-20261104 https://github.com/esi-ubuntu/ERP.git
cd ERP
python3 -m unittest discover -s tests -v
bash -n deploy/scripts/*.sh
```

Follow [the complete colleague handoff](deploy/README.md) to build and inspect the image first, then separately initialize a new isolated site. The tracked upstream ERPNext source is a Git submodule. The deployment uses a custom Docker image instead of editing upstream source. Do not use `compose.demo.yml` for a public environment; it contains disposable demo credentials.

## Current evidence

- Image construction and four-app site installation: **not yet executed on an isolated server**.
- ERPNext core group accounting and Projects: available upstream, not yet mapped one-to-one to all customer requirements.
- HRMS: upstream v16 release selected.
- Iranian localization: pinned to a commit with passing v16 integration CI, but tax and payroll legal acceptance remains pending.
- `bisness_core`: version 0.1.0 Frappe app skeleton; consolidation, intercompany elimination and central treasury are **not implemented**.
- No merge, deploy, migration or production traffic has been performed by this repository change.

Upstream: [Frappe ERPNext](https://github.com/frappe/erpnext), [Frappe HRMS](https://github.com/frappe/hrms), [Iran localization candidate](https://github.com/bijanshdevops/erpnext_iran), [Official Frappe Docker](https://github.com/frappe/frappe_docker).

