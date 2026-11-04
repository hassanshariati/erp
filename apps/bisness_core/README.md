# Bisness Core

Reusable Frappe/ERPNext app for organizations, regardless of their legal name or domain.

- Python app / Bench installation name: `bisness_core`.
- Product component label: `bisness-core`.
- Depends on ERPNext v16 and Frappe HRMS v16; the deployment also includes the evaluated Iranian localization `erpnext_iran`.
- This first revision contains a clean installable app boundary and dependency declaration. It does **not** claim that finance consolidation, intercompany elimination, payroll compliance, or treasury automation are implemented.
- No customer company, tenant, national identifier, bank account, fiscal policy, site domain, or legal rate is seeded.
- Customer-specific requirements live in documentation and site-level configuration; they are never constants in this app.
- License for this first-party app is intentionally not declared until the product owner decides its commercial distribution terms and reviews ERPNext's applicable GPL obligations.

Future functions must be driven by verified generic use cases, security tests, and independently configured companies/sites.
