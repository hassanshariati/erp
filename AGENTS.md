# ERP project agent instructions

## Customer-independent product rules

- The product is intended for multiple independent customers, not one named organization. Do not hard-code any customer name, domain, company tree, employee identifier, bank details, fiscal policy or statutory rate in runtime source, Dockerfiles, Compose, or app defaults.
- This repository's first-party Frappe application is **`bisness_core`** (product label `bisness-core`). Do not create a `vira_core` alias.
- Customer RFPs are source documents under `docs/requirements/`; their IDs and company maps belong to the **specific customer**, not a global product registry or seeded master data.
- Validate each feature against generic acceptance scenarios, then optionally link it to one or more customer-specific requirements. Customer sign-off and Microsoft-ecosystem constraints cannot be assumed resolved.
- Treat HRMS, Iranian localization, intercompany eliminations, group treasury and payroll compliance as unverified until tested. A green CI does not certify compliance with the Iranian Tax Organization.
- No production deploy, site migration, credential movement or Action run without an explicitly approved operational change.

## Graph-first → Source-last

0. The hand-maintained product component graph is `docs/architecture/product-components.json`. It is not generated evidence and must never be described as runtime proof.
1. Check `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md` before architecture or change-impact work.
2. If current, use `graphify query` (or path/explain) to locate the minimum relevant source, then verify against code and tests.
3. If missing or stale, state that explicitly; follow `.graphify/README.md` to regenerate locally. Never hand-edit generated graph files.
4. The `upstream/erpnext` submodule is not necessarily checked out. A code-only graph of deployment files or `bisness_core` does not describe ERPNext internals.
5. Keep .env, credentials, database/site volumes, backups, generated assets and private user data outside Graphify input and Git.

## Safety

- Preserve existing customer requirement records and their source hashes; do not rewrite history or convert customer-specific RFP wording to generic claims.
- On shared servers, do not touch unrelated projects, services or listener ports.
- Graphify CI is manual-only. Never run it automatically to satisfy a code change.
