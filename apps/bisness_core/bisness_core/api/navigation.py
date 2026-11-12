"""Permissions for the Business Core entry in the Frappe v16 Apps desktop."""

import frappe


def check_app_permission():
    """Only Desk administrators see the Business Settings app entry.

    Business Branding Settings is a System Manager-only Single DocType. Do not
    advertise an otherwise inaccessible workspace to ordinary users.
    """
    user = frappe.session.user
    if user == "Administrator":
        return True
    if not user or user == "Guest":
        return False
    return "System Manager" in frappe.get_roles(user)
