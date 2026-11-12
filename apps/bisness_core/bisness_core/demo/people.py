"""Create fictional, individually named ERP contacts, leads and employees.

Never run automatically or create user accounts/credentials, phone numbers or
email addresses. Only operates with explicit demo-company opt-in.
"""

import frappe

from bisness_core.demo.seed import _must_be_demo_company, _save_new, DEMO_PREFIX

FIRST_NAMES = (
    "Arman", "Nima", "Parsa", "Darya", "Sahar", "Leila", "Mina", "Kian",
    "Amir", "Roya", "Navid", "Sara", "Yasmin", "Pouya", "Tara", "Reza",
    "Farid", "Shirin", "Niloofar", "Sam", "Mahan", "Hoda", "Mahtab", "Kaveh",
    "Oliver", "Isabella", "Sophia", "Liam", "Emma", "Noah", "Aisha", "Omar",
    "Fatima", "Zain", "Priya", "Ravi", "Mei", "Chen", "Kenji", "Hana",
    "Layla", "Nour", "Daniel", "Maria", "Nadia", "Alex", "Yusuf", "Elena",
)
LAST_NAMES = (
    "Rahimi", "Karimi", "Farhadi", "Ahmadi", "Moradi", "Jafari", "Rostami",
    "Soleimani", "Kazemi", "Mohammadi", "Ebrahimi", "Ghasemi", "Hosseini",
    "Mahdavi", "Hedayati", "Nikfar", "Sadeghi", "Mehrabi", "Rashidi", "Azimi",
    "Bennett", "Walker", "Turner", "Carter", "Evans", "Khan", "Malik",
    "Haddad", "Sharma", "Patel", "Chen", "Tanaka", "Garcia", "Silva",
    "Andersson", "Novak",
)
COMPANY_WORDS = (
    "Caspian", "Atlas", "Horizon", "Bluewater", "Summit", "Aurora",
    "Meridian", "Pioneer", "Cobalt", "Nimbus", "Orion", "Granite",
    "Redwood", "Northstar", "Delta", "Sunrise", "Evergreen", "Helix",
)
COMPANY_SERVICES = (
    "Energy", "Field Services", "Petrochemicals", "Marine Logistics",
    "Subsea Technology", "Drilling Solutions", "Industrial Supply",
    "Engineering", "Equipment", "Energy Trading",
)
JOBS = (
    "Field Engineer", "Production Planner", "Maintenance Coordinator",
    "HSE Specialist", "Logistics Manager", "Operations Analyst",
    "Procurement Officer", "Process Engineer", "Commercial Manager",
    "Project Coordinator", "Well Integrity Specialist", "Field Supervisor",
)


def demo_person(index):
    """Return a natural-looking, repeatable name, unique for indexes 1..1728."""
    number = int(index) - 1
    if not (0 <= number < len(FIRST_NAMES) * len(LAST_NAMES)):
        frappe.throw("Demo person index out of range")
    return FIRST_NAMES[number % len(FIRST_NAMES)], LAST_NAMES[number // len(FIRST_NAMES)]


def _more_companies(counter, warnings):
    """Create demo-only names; do not mutate or alias real counterparties."""
    customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
    supplier_group = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
    territory = frappe.db.get_value("Territory", {"is_group": 0}, "name")
    if not (customer_group and supplier_group and territory):
        frappe.throw("Customer Group, Supplier Group and Territory are required")
    for index in range(1, 81):
        word = COMPANY_WORDS[(index - 1) % len(COMPANY_WORDS)]
        sector = COMPANY_SERVICES[((index - 1) // len(COMPANY_WORDS)) % len(COMPANY_SERVICES)]
        customer_name = f"{DEMO_PREFIX}{word} {sector} Client {index:03}"
        supplier_name = f"{DEMO_PREFIX}{word} {sector} Partner {index:03}"
        _save_new("Customer", {"customer_name": customer_name}, {
            "customer_name": customer_name, "customer_type": "Company",
            "customer_group": customer_group, "territory": territory,
        }, counter, warnings)
        _save_new("Supplier", {"supplier_name": supplier_name}, {
            "supplier_name": supplier_name, "supplier_type": "Company",
            "supplier_group": supplier_group,
        }, counter, warnings)


def _demo_party_links():
    customers = frappe.get_all(
        "Customer", filters={"customer_name": ["like", "[DEMO] %"]},
        pluck="name", limit_page_length=500, order_by="name",
    )
    suppliers = frappe.get_all(
        "Supplier", filters={"supplier_name": ["like", "[DEMO] %"]},
        pluck="name", limit_page_length=500, order_by="name",
    )
    parties = [("Customer", name) for name in customers] + [
        ("Supplier", name) for name in suppliers
    ]
    if not parties:
        frappe.throw("Cannot link contacts: no [DEMO] customers or suppliers exist")
    return parties


def _open_crm_status():
    if not frappe.db.exists("DocType", "CRM Lead"):
        return None
    status = frappe.get_all(
        "CRM Lead Status", filters={"type": "Open"},
        pluck="name", order_by="name", limit_page_length=20,
    )
    if "New" in status:
        return "New"
    return status[0] if status else None


def expand_demo_people(confirm=None, company=None):
    """Opt-in only. Add 720 Contacts, 360 ERP Leads, 360 CRM Leads, 120 Employees.

    Safe to rerun: records carry a DEMO-OG key in company/organization/designation.
    Uses no real-looking contact details and never creates logins or payroll.
    """
    if confirm != "EXPAND_OIL_GAS_DEMO":
        frappe.throw("Confirmation EXPAND_OIL_GAS_DEMO is required")
    _must_be_demo_company(company)
    counter, warnings = {"attempted": 0}, []
    _more_companies(counter, warnings)
    parties = _demo_party_links()

    for index in range(1, 721):
        first, last = demo_person(index)
        doctype, party = parties[(index - 1) % len(parties)]
        marker = f"DEMO-OG-PERSON-{index:04}"
        _save_new("Contact", {"designation": marker}, {
            "first_name": first, "last_name": last,
            "designation": marker,
            "status": "Open",
            "links": [{"link_doctype": doctype, "link_name": party}],
            "company_name": party,
        }, counter, warnings)

    for index in range(1, 361):
        first, last = demo_person(index + 720)
        organization = f"{DEMO_PREFIX}Oil & Gas Prospect OG-{index:04}"
        _save_new("Lead", {"company_name": organization}, {
            "first_name": first, "last_name": last, "lead_name": f"{first} {last}",
            "company_name": organization, "status": "Lead",
        }, counter, warnings)

    crm_status = _open_crm_status()
    if crm_status:
        for index in range(1, 361):
            first, last = demo_person(index + 1080)
            organization = f"{DEMO_PREFIX}Oil & Gas CRM Prospect OG-{index:04}"
            _save_new("CRM Lead", {"organization": organization}, {
                "first_name": first, "last_name": last,
                "organization": organization,
                "status": crm_status,
                "job_title": JOBS[(index - 1) % len(JOBS)],
                "lead_temperature": ("Cold", "Warm", "Hot")[index % 3],
            }, counter, warnings)
    else:
        warnings.append("CRM open-type Lead Status missing; no CRM leads created")

    gender = frappe.db.get_value("Gender", {}, "name") if frappe.db.exists("DocType", "Gender") else None
    if gender and frappe.db.exists("DocType", "Employee"):
        for index in range(1, 121):
            first, last = demo_person(index + 1440)
            _save_new("Employee", {
                "first_name": first, "last_name": last, "company": company,
            }, {
                "first_name": first, "last_name": last,
                "company": company, "gender": gender,
                "date_of_birth": f"19{80 + index % 18:02}-05-14",
                "date_of_joining": "2025-01-15",
                "status": "Active",
            }, counter, warnings)
    else:
        warnings.append("Employee or Gender master missing; no new HR demo employees")

    frappe.db.commit()
    return {
        "demo_company": company,
        "created": {k: v for k, v in counter.items() if k != "attempted"},
        "total_demo_contacts": frappe.db.count("Contact", {"designation": ("like", "DEMO-OG-PERSON-%")}),
        "demo_crm_status": crm_status,
        "warnings": warnings,
    }
