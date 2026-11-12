# Oil & gas ERP demo (synthetic data only)

This branch adds a **deliberately opt-in** industry demo pack for the existing
first-party Frappe app `bisness_core`. Nothing here seeds customers or actual
financial data during `bench migrate`, initial site installation, or normal app
startup. All demo records use the `[DEMO]` or `DEMO-OG-` namespace.

## Intended user journey

* **Business Settings** workspace and its **Login Branding** sidebar entry
  open the **Business Branding Settings** Single DocType. Change brand name,
  public logo, accent color, and login image/animation there.
* **Selling**: synthetic customer and prospect lists, draft sales orders.
* **Buying**: 36 synthetic vendors, draft purchase orders.
* **Stock**: 20 oilfield material/service examples (no stock balance is posted).
* **Projects**: 10 development/maintenance projects and 60 linked work packages.
* **HRMS**: up to 48 fictional employees, with no actual account or payroll data.
* **Frappe CRM**: up to 120 CRM leads, 30 CRM organizations, 30 deals and 30
  follow-up tasks (requires configured CRM status masters).
* **Operations**: 12 fictional assets, 365 days per asset = **4,380**
  operational KPI rows. Data includes production BOE, oil barrels, natural gas
  Mscf, downtime, expected revenue and cost, emissions, water cut, HSE near
  misses, crew and maintenance.
* **Insights v3**: creates a **private** workbook named
  `[DEMO] Oil & Gas | Executive Intelligence` and dashboard named
  `[DEMO] Oil & Gas | Executive Command Center` containing 10 executive
  number cards and 8 detailed visualizations. The charts are built on
  `tabDemo Oil Gas KPI` in the site's own database, using live connection.
* **Wiki**: existing wiki application remains unchanged. Do not claim demo
  articles exist unless they are explicitly authored/imported on the demo site.
* **Finance**: dashboard `revenue_usd` and `opex_usd` are **simulated
  operational estimates**, not ERPNext posted general ledger transactions.
  Draft documents do not produce real accounting balances.

## Required sandbox setup, not on production

1. Provision a separate **disposable, isolated** ERPNext v16 demo site with
   the same first-party app, HRMS, CRM and Insights pinned in the repository.
   Follow the site's existing backup, privacy and tenant policy.
2. Complete ERPNext Setup Wizard on that isolated site. Create the **new**
   company `[DEMO] Oil & Gas Operations`; assign its chart of accounts and
   standard masters (UOM, Customer Group, Supplier Group, Item Group,
   Territory). Never reuse an actual customer company or payroll account.
3. Install/migrate the updated first-party app and initialize Insights v3
   including the **Site DB** data source. Grant an authorized demo account
   `Insights Admin` and `System Manager` as appropriate. Verify the source
   can access the `Demo Oil Gas KPI` table.
4. An authorized operator then explicitly opts in on **that demo site only**:

   ```bash
   bench --site demo.local set-config enable_oil_gas_demo_seed 1
   bench --site demo.local execute bisness_core.demo.seed.seed_demo \
     --kwargs '{"confirm":"SEED_OIL_GAS_DEMO","company":"[DEMO] Oil & Gas Operations","days":365}'
   ```

   The generated data is repeatable and inserts are idempotent by the
   `DEMO-OG` IDs and demo record lookups. The command returns created counts,
   warnings for optional masters and the Insights workbook/dashboard IDs.

5. Verify at least these checks **on staging** (the CLI seed does not prove
   that they all work in production):
   * Company scoping and permissions; rerun seed and ensure no duplicate KPIs.
   * All requested master lists plus Projects, HRMS and CRM pages.
   * Insights dashboard loads all **18** cards/charts and KPI aggregates.
   * The published login endpoint returns only explicitly public uploaded
     images and a cache-version; test an image change, a new logo, a private
     upload rejection, and mobile rendering.
   * Confirm that there are **no submitted** Sales Orders/Purchase Orders and
     **no new** GL Entries, Stock Ledger Entries, Salary Slips or Payment Entries
     caused by the demo generator.
   * Ensure other sites/companies have not been changed.

The UI shortcut after an isolated staging install is **Business Settings**
(from the Desk sidebar/workspace), then **Business Branding Settings**.

### Manual sanity check

```bash
bench --site demo.local execute frappe.db.count --args '["Demo Oil Gas KPI"]'
bench --site demo.local execute frappe.db.get_value \
  --args '["Insights Workbook",{"title":"[DEMO] Oil & Gas | Executive Intelligence"},"name"]'
```

## Safety and limits

* The built-in seed requires an explicit **confirmation string**, a **site
  config opt-in flag** (disabled by default), and a company name beginning
  `[DEMO]` that must already exist. It is **never** run by an install,
  patch, background job or GitHub Action.
* Do not run a schema migration or demo seed on the live `armember.ir`
  database under the assumption that this branch alone approves a release.
  Confirm maintenance window, verified backup and restore path, and review
  existing customer data before any production release.
* Source code must remain customer-agnostic. All fictional entities appear
  **only** in the explicitly opted-in demo package.
* All monetary, oilfield, climate and HSE values are synthetic and do not
  certify reserve, accounting, safety, environmental or legal compliance.
* User accounts, credentials, bank data, Iranian tax/payroll rates and
  payments are intentionally **not** created.
* The seeder reports validation warnings if optional ERPNext/CRM structures
  are missing. Fix staging setup and rerun; do not work around validations
  by writing directly into protected customer tables.
* A standard backup/restore of the **disposable demo site**, rather than
  deleting by unscoped criteria, is the intended way to reset the demo.
