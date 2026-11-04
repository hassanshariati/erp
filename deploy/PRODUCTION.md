# Production release gate — customer-independent

No production release is approved by the existence of these deployment files.

## Per-instance inputs

- `SITE_NAME`, `CUSTOM_IMAGE`, `CUSTOM_TAG`, `HOST_HTTP_PORT` in a private `deploy/.env`.
- DB/admin secrets generated outside Git; encryption, retention and restore test for offsite backups.
- External DNS, domain ownership, TLS/ACME mailbox and reverse-proxy topology.
- The legal companies, banks, tax rules, roles and approval matrices configured as site data after customer sign-off.

## Required verification

1. Build/pin a custom image and inspect its software bill of materials and dependencies. The current pins are version/SHA references, not accepted registry digests.
2. Install the four apps on a **disposable** ERPNext v16 site. Record exact versions, migrations and a smoke test for HRMS and `erpnext_iran`.
3. Validate account boundaries, access controls and backups before collecting live company or employee data.
4. Verify Iranian statutory tax and insurance calculations with accountable specialists, and Moadian API workflows with authorized test credentials.
5. Confirm business procedures and contracts. A customer RFP is a requirement input, not an automatic product feature.
6. Plan the HTTPS listener around current host port users. Never expose DB/Redis or private HTTP ports.
7. For upgrades to sites that already exist, use a separately reviewed backup + migration + rollback procedure. `scripts/initialize.sh` is **new-site-only**.

No CI pipeline, public service, image push or live database migration is triggered by this documentation change.
