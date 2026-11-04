# Generic ERPNext Product Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for implementation. All checkboxes reflect Git-source status only; integration gates remain incomplete.

**Goal:** Add ERPNext v16 + official HRMS + experimental Iranian localization + reusable `bisness_core` without customer identifiers in runtime code.

**Architecture:** Keep ERPNext unmodified. Build one local image with pinned third-party app refs and the first-party app copied from this repository. Install only into a brand-new disposable site; keep customer-specific RFP evidence separate.

**Tech Stack:** ERPNext/Frappe v16.53.0, Python 3.14, HRMS v16.53.0, `erpnext_iran`, Docker/Compose, Caddy.

**Spec:** `docs/architecture/product-core.md`

## Global constraints

- Product component spelled `bisness-core`, Frappe app/module `bisness_core`.
- No static company names, real domains, passwords, national IDs or tax rates.
- No automatic install/migration of an existing site.
- No public listener or change to existing services on the shared VPS.
- No unverified legal or fiscal behavior claimed as implemented.

## Review focus

1. Missing `.env` or invalid `SITE_NAME` → refuse.
2. Existing site → do not install apps or run DB migration.
3. Moving upstream branch → image build rejects changed SHA.
4. Host HTTP port conflict → loopback-only configurable port.
5. Legal rules/data unknown → no seeded company or tax policy.

## Work items

### Task 1: Generic Frappe app

- [x] Add Python metadata and Frappe hooks for `bisness_core`.
- [x] Declare explicit ERPNext, HRMS and Iran add-on dependencies.
- [x] Add contract tests rejecting customer literals.
- [ ] Build and install the app on disposable Frappe v16 site.

### Task 2: Custom four-app image

- [x] Extend the pinned ERPNext image with HRMS, Iran localization and local core app.
- [x] Verify upstream Git SHAs in build instructions.
- [ ] Perform an actual Docker build and record the resulting image digest.

### Task 3: Parameterized private deployment

- [x] Remove customer names and network specifics from Compose, Caddy, .env template and initialization script.
- [x] Refuse existing-site installs without a separately approved upgrade.
- [ ] Execute `docker compose config` and a disposable installation test.

### Task 4: Documentation and traceability

- [x] Make product docs customer-independent while preserving RFP evidence.
- [x] Document remaining functional gaps and legal/commercial licensing gate.
- [ ] Obtain formal approval of statutory integration and the product distribution license.

## Current verification

Static source checks are supplied in `tests/test_product_contract.py`. They do not substitute for Docker/Bench integration testing. No production deployment was authorized or executed.
