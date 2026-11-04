# Graphify — reusable ERP product

Purpose: a local, queryable graph of application code/configuration. Permanent policy: **Graph-first → Source-last**.

## Coverage

The repository has deployment files, the first-party `apps/bisness_core` app, and a Git submodule pointer to upstream ERPNext. A Graphify run over a normal checkout does not include ERPNext internals unless `upstream/erpnext` is initialized.

- Automatic GitHub workflow is **manual-only** (`workflow_dispatch`), with no deploy or PR side effects.
- `.graphifyignore` excludes credentials, sites, backup files, generated assets and customer documents.
- Code graphs do not prove runtime behavior, financial correctness, licensing or legal compliance.

## Local run

```bash
bash scripts/graphify.sh
```

The script sets up an isolated Python environment and runs pinned `graphifyy==0.9.67` in code-only mode. It writes:

- `graphify-out/graph.json`
- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.html`

Before querying, check whether these outputs exist and correspond to the current branch. If the ERPNext submodule is uninitialized, explain that limitation rather than inventing source-level evidence.

## Customer evidence is separate

The business requirement graph at `docs/architecture/requirements-graph.json` and the customer-specific RFP at `docs/requirements/` are **not generated Graphify output** and do not encode default product behavior. Use their source IDs only when assessing that customer's proposal. General product architecture is documented in `docs/architecture/product-core.md`.

No Graphify run was dispatched while preparing this product baseline.
