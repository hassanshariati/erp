"""Explicit, idempotent, staging-only industry demo seeder.

NEVER invoked by install, migration, patch, scheduler, import, or web endpoints.
No live financial, stock or payroll postings: orders/requests remain drafts.
"""

from datetime import date, timedelta
from itertools import islice

import frappe

from bisness_core.demo.oil_gas_dataset import ASSETS, PRODUCTS, PROJECTS, generate_daily_kpis
from bisness_core.demo.insights_dashboard import install_insights_dashboard


CONFIRMATION = "SEED_OIL_GAS_DEMO"
DEMO_PREFIX = "[DEMO] "
END_DATE = date(2026, 10, 31)


def _must_be_demo_company(company):
    if not isinstance(company, str) or not company.startswith(DEMO_PREFIX):
        frappe.throw("Company must begin with [DEMO] and must not be a live company.")
    if not frappe.db.exists("Company", company):
        frappe.throw(
            "Create a new, isolated demo company in ERPNext Setup first: " + company
        )
    if not frappe.conf.get("enable_oil_gas_demo_seed"):
        frappe.throw(
            "Demo seed is disabled. Enable site config enable_oil_gas_demo_seed "
            "ONLY on an isolated disposable demonstration site."
        )


def _choose_leaf(doctype):
    return frappe.db.get_value(doctype, {"is_group": 0}, "name")


def _save_new(doctype, lookup, data, counter, warnings):
    """Insert only new demo-tagged records; keep optional failures visible."""
    existing = frappe.db.exists(doctype, lookup)
    if existing:
        return existing
    idx = counter["attempted"]
    counter["attempted"] += 1
    savepoint = "demo_seed_" + str(idx)
    frappe.db.savepoint(savepoint)
    try:
        doc = frappe.get_doc({"doctype": doctype, **data})
        doc.insert(ignore_permissions=True)
        counter[doctype] = counter.get(doctype, 0) + 1
        return doc.name
    except Exception as exc:
        frappe.db.rollback(save_point=savepoint)
        if len(warnings) < 40:
            warnings.append(f"{doctype}: {type(exc).__name__}: {str(exc)[:180]}")
        return None


def _batch_insert_kpis(company, days):
    """Insert synthetic KPI records in bounded batches, without creating GL/stock entries."""
    columns = [
        "name", "owner", "creation", "modified", "modified_by", "docstatus", "idx",
        "record_id", "production_date", "company", "asset", "region", "product_line",
        "planned_boe", "actual_boe", "oil_bbl", "gas_mscf", "revenue_usd", "opex_usd",
        "downtime_hours", "water_cut_pct", "emissions_tco2e", "hse_events",
        "work_orders", "crew",
    ]
    now = frappe.utils.now()
    actor = frappe.session.user or "Administrator"
    total = 0
    generated = generate_daily_kpis(company, end_date=END_DATE, days=days)
    while True:
        batch = list(islice(generated, 250))
        if not batch:
            break
        rows = []
        for record in batch:
            rows.append([
                record["record_id"], actor, now, now, actor, 0, 0,
                *[record.get(key) for key in columns[7:]],
            ])
        frappe.db.bulk_insert(
            "Demo Oil Gas KPI", columns, rows, ignore_duplicates=True,
        )
        total += len(rows)
    return total


def _seed_erp_masters(company, count, warnings):
    """Create master data and project/task examples under the demo namespace."""
    item_group = _choose_leaf("Item Group")
    customer_group = _choose_leaf("Customer Group")
    supplier_group = _choose_leaf("Supplier Group")
    territory = frappe.db.get_value("Territory", {"is_group": 0}, "name")
    uom = "Nos" if frappe.db.exists("UOM", "Nos") else frappe.db.get_value("UOM", {}, "name")
    if not (item_group and customer_group and supplier_group and territory and uom):
        frappe.throw("Finish ERPNext setup: Item, Customer, Supplier, Territory and UOM masters required")

    customers, suppliers, items, projects = [], [], [], []
    for n in range(1, 25):
        name = f"{DEMO_PREFIX}Energy Buyer {n:03}"
        result = _save_new("Customer", {"customer_name": name}, {
            "customer_name": name,
            "customer_type": "Company", "customer_group": customer_group, "territory": territory,
        }, count, warnings)
        if result: customers.append(result)

    for n in range(1, 37):
        name = f"{DEMO_PREFIX}Oilfield Supplier {n:03}"
        result = _save_new("Supplier", {"supplier_name": name}, {
            "supplier_name": name, "supplier_type": "Company", "supplier_group": supplier_group,
        }, count, warnings)
        if result: suppliers.append(result)

    for n, name in enumerate(PRODUCTS, 1):
        code = f"DEMO-OG-ITEM-{n:03}"
        result = _save_new("Item", {"item_code": code}, {
            "item_code": code,
            "item_name": f"{DEMO_PREFIX}{name}",
            "description": f"Fictional demo inventory: {name}",
            "item_group": item_group, "stock_uom": uom,
            "is_stock_item": 1, "standard_rate": float(200 + n * 43),
        }, count, warnings)
        if result: items.append(result)

    for n, title in enumerate(PROJECTS, 1):
        project_name = f"{DEMO_PREFIX}{n:02} | {title}"
        result = _save_new("Project", {"project_name": project_name, "company": company}, {
            "project_name": project_name,
            "company": company,
            "naming_series": "PROJ-.####",
            "status": "Open" if n % 4 != 0 else "Completed",
            "expected_start_date": (END_DATE - timedelta(days=160+n*6)).isoformat(),
            "expected_end_date": (END_DATE + timedelta(days=80+n*5)).isoformat(),
        }, count, warnings)
        if result: projects.append(result)

    for n in range(1, 101):
        first = "Demo"
        last = f"Energy Prospect {n:03}"
        _save_new("Lead", {"first_name": first, "last_name": last, "company_name": f"{DEMO_PREFIX}Prospect {n:03}"}, {
            "first_name": first, "last_name": last,
            "lead_name": f"{first} {last}",
            "company_name": f"{DEMO_PREFIX}Prospect {n:03}",
            "status": ["Lead", "Open", "Replied", "Interested"][n % 4],
        }, count, warnings)

    for n in range(1, 61):
        if not projects: break
        subject = f"{DEMO_PREFIX}Work Package {n:03} — {PROJECTS[(n-1) % len(PROJECTS)]}"
        _save_new("Task", {"subject": subject, "project": projects[(n-1) % len(projects)]}, {
            "subject": subject,
            "project": projects[(n-1) % len(projects)],
            "status": ["Open", "Working", "Pending Review", "Completed"][n % 4],
            "priority": ["Low", "Medium", "High"][n % 3],
        }, count, warnings)

    gender = frappe.db.get_value("Gender", {}, "name") if frappe.db.exists("DocType", "Gender") else None
    if gender and frappe.db.exists("DocType", "Employee"):
        for n in range(1, 49):
            first, last = "Demo", f"Operations Employee {n:03}"
            _save_new("Employee", {"first_name": first, "last_name": last, "company": company}, {
                "first_name": first, "last_name": last, "company": company,
                "gender": gender,
                "date_of_birth": "1990-01-01",
                "date_of_joining": "2024-01-01",
                "status": "Active",
            }, count, warnings)
    else:
        warnings.append("Employee examples omitted: the Gender or Employee master is missing")

    # Optional procurement and sales drafts only. Never submit, book, pay or stock.
    for n in range(1, 13):
        if customers and items:
            customer = customers[(n - 1) % len(customers)]
            item = items[(n - 1) % len(items)]
            po_no = f"DEMO-OG-SO-{n:03}"
            _save_new("Sales Order", {"po_no": po_no, "company": company}, {
                "customer": customer, "company": company,
                "transaction_date": "2026-10-31",
                "delivery_date": "2026-12-15",
                "po_no": po_no,
                "items": [{"item_code": item, "qty": 2 + n, "rate": 550 + n * 100,
                           "delivery_date": "2026-12-15"}],
            }, count, warnings)
        if suppliers and items:
            supplier = suppliers[(n - 1) % len(suppliers)]
            item = items[(n+3) % len(items)]
            remarks = f"DEMO-OG-PO-{n:03} — draft only"
            _save_new("Purchase Order", {"remarks": remarks, "company": company}, {
                "supplier": supplier, "company": company,
                "transaction_date": "2026-10-31",
                "schedule_date": "2026-12-15",
                "remarks": remarks,
                "items": [{"item_code": item, "qty": 5 + n, "rate": 400 + n * 70,
                           "schedule_date": "2026-12-15"}],
            }, count, warnings)
    return {"customers": len(customers), "suppliers": len(suppliers),
            "items": len(items), "projects": len(projects)}


def _seed_crm(count, warnings):
    """Populate the separately installed Frappe CRM without touching ERP sales."""
    if not frappe.db.exists("DocType", "CRM Lead"):
        warnings.append("Frappe CRM not installed; CRM-specific examples skipped")
        return
    # A random first status can be 'Lost' and requires a lost reason.
    # Choose only an open pipeline status for newly generated leads/deals.
    lead_status = frappe.db.get_value("CRM Lead Status", {"type": "Open"}, "name")
    deal_status = frappe.db.get_value("CRM Deal Status", {"type": "Open"}, "name")
    if not lead_status:
        warnings.append("CRM Lead Status not configured; CRM examples skipped")
        return
    for n in range(1, 121):
        org = f"{DEMO_PREFIX}Energy Account {n:03}"
        _save_new("CRM Lead", {"organization": org, "first_name": "Demo", "last_name": f"Contact {n:03}"}, {
            "first_name": "Demo", "last_name": f"Contact {n:03}",
            "organization": org, "status": lead_status,
            "job_title": ["Operations Director", "Procurement Lead", "Field Manager"][n % 3],
        }, count, warnings)
    if not deal_status:
        warnings.append("CRM Deal Status not configured; CRM deals skipped")
        return
    for n in range(1, 31):
        org_name = f"{DEMO_PREFIX}CRM Operator {n:03}"
        org = _save_new("CRM Organization", {"organization_name": org_name}, {
            "organization_name": org_name,
            "company_description": "Synthetic oil and gas enterprise account",
        }, count, warnings)
        if org:
            _save_new("CRM Deal", {"organization": org}, {
                "organization": org, "status": deal_status,
                "expected_deal_value": 150000 + 18000 * n,
                "deal_value": 120000 + 13000 * n,
            }, count, warnings)
    if frappe.db.exists("DocType", "CRM Task"):
        for n in range(1, 31):
            title = f"{DEMO_PREFIX}Follow up oilfield prospect {n:03}"
            _save_new("CRM Task", {"title": title}, {
                "title": title, "status": ["Backlog", "Todo", "In Progress", "Done"][n % 4],
                "priority": ["Low", "Medium", "High"][n % 3],
                "due_date": (END_DATE + timedelta(days=n)).isoformat(),
            }, count, warnings)


def seed_demo(confirm=None, company="[DEMO] Oil & Gas Operations", days=365):
    """Run only with explicit site opt-in and confirmation on a disposable site.

    Example:
      bench --site demo.local execute bisness_core.demo.seed.seed_demo --kwargs
      '{"confirm":"SEED_OIL_GAS_DEMO","company":"[DEMO] Oil & Gas Operations"}'
    """
    if confirm != CONFIRMATION:
        frappe.throw("Explicit confirmation required: SEED_OIL_GAS_DEMO")
    _must_be_demo_company(company)
    days = int(days)
    if not (30 <= days <= 730):
        frappe.throw("days must be between 30 and 730")
    if not frappe.db.exists("DocType", "Demo Oil Gas KPI"):
        frappe.throw("Missing Demo Oil Gas KPI DocType; run bench migrate first")

    counter, warnings = {"attempted": 0}, []
    counts = _seed_erp_masters(company, counter, warnings)
    _seed_crm(counter, warnings)
    kpi_processed = _batch_insert_kpis(company, days)
    try:
        dashboard = install_insights_dashboard()
    except Exception as exc:
        # KPI data is still useful even if Insights has not yet been configured.
        dashboard = {"error": f"{type(exc).__name__}: {str(exc)[:200]}"}
    frappe.db.commit()
    return {
        "demo_only": True,
        "company": company,
        "kpi_processed": kpi_processed,
        "kpi_total": frappe.db.count("Demo Oil Gas KPI", {"company": company}),
        "created": {k: v for k, v in counter.items() if k != "attempted"},
        "masters_found": counts,
        "insights": dashboard,
        "warnings": warnings,
    }
