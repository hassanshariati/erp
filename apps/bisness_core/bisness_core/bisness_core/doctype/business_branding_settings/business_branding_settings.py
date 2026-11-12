"""Editable per-site branding with clear upload feedback.

Only public files may be displayed on a guest login page. Never publish
private uploads automatically, because that may expose confidential files.
"""

import frappe
from frappe.model.document import Document

from bisness_core.api.branding import (
    _IMAGE_SUFFIXES, _VIDEO_SUFFIXES, _public_media_url,
)


class BusinessBrandingSettings(Document):
    def validate(self):
        self._validate_public_file("brand_logo", _IMAGE_SUFFIXES)
        self._validate_public_file("animation_file", _IMAGE_SUFFIXES | _VIDEO_SUFFIXES)

    def _validate_public_file(self, fieldname, suffixes):
        value = self.get(fieldname)
        if not value:
            return
        label = self.meta.get_label(fieldname) or fieldname
        url = _public_media_url(value, suffixes)
        if not url:
            frappe.throw(
                f"{label}: use a local PUBLIC image or video with a supported extension."
            )
        if url.startswith("/assets/"):
            return
        file_info = frappe.db.get_value(
            "File", {"file_url": url}, ["name", "is_private"], as_dict=True
        )
        if not file_info:
            frappe.throw(
                f"{label}: the uploaded file was not found in File records."
            )
        if file_info.is_private:
            frappe.throw(
                f"{label}: this file is PRIVATE. Re-upload with 'Private' "
                "unchecked in the upload dialog, then Save. Guest login pages "
                "cannot display private attachments."
            )
