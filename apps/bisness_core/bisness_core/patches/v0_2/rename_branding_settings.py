"""Rename the display DocType while keeping the internal app identifier bisness_core.

Runs before DocType schema synchronization. Never erase tenant-owned uploads or
replace field contents; both versions are Single DocTypes (tabSingles).
"""

import frappe


OLD = "Bisness Branding Settings"
NEW = "Business Branding Settings"
FIELDS = ("brand_name", "brand_tagline", "brand_logo", "accent_color", "animation_file")


def execute():
    if not frappe.db.exists("DocType", OLD):
        return
    # Keep a copy in memory even when Frappe's rename handles tabSingles.
    prior = dict(
        frappe.db.sql(
            "select field, value from tabSingles where doctype = %s",
            OLD,
            as_list=True,
        )
    )
    if not frappe.db.exists("DocType", NEW):
        frappe.rename_doc("DocType", OLD, NEW, force=True)
    # Some framework versions do not move Single values with DocType metadata.
    for field in FIELDS:
        if field in prior and frappe.db.get_single_value(NEW, field) in (None, ""):
            frappe.db.set_single_value(NEW, field, prior[field])
    frappe.clear_cache(doctype=NEW)
