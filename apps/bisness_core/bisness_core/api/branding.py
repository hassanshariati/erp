"""Read-only public login branding. Never expose private tenant File records."""

import re
from hashlib import sha256
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

import frappe


_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"}
_VIDEO_SUFFIXES = {".mp4", ".webm"}
_DEFAULT_COLOR = "#35C991"


def _public_media_url(value, allowed_suffixes):
    """Accept only same-origin public paths with a supported extension."""
    if not isinstance(value, str) or len(value) > 1024:
        return ""
    value = value.strip()
    if not value or "\\" in value or any(ord(char) < 32 for char in value):
        return ""
    parts = urlsplit(value)
    if parts.scheme or parts.netloc or parts.query or parts.fragment:
        return ""
    path = unquote(parts.path)
    segments = path.split("/")
    if (
        not path.startswith(("/files/", "/assets/"))
        or any(part in ("", ".", "..") for part in segments[1:])
        or "\\" in path
        or any(ord(char) < 32 for char in path)
    ):
        return ""
    return value if PurePosixPath(path).suffix.lower() in allowed_suffixes else ""


def _public_asset(value, allowed_suffixes):
    """Return (URL, version). For uploaded files, verify the File is public."""
    url = _public_media_url(value, allowed_suffixes)
    if not url:
        return "", ""
    if not url.startswith("/files/"):
        return url, ""
    # A bare /files/ URL alone does not prove an attachment is public.
    modified = frappe.db.get_value(
        "File", {"file_url": url, "is_private": 0}, "modified"
    )
    if not modified:
        return "", ""
    # Changing an upload at the same URL must invalidate the browser cache.
    version = sha256(str(modified).encode("utf-8")).hexdigest()[:12]
    return url, version


def _safe_color(value):
    if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value.strip()):
        return value.strip()
    return _DEFAULT_COLOR


def _safe_label(value, length):
    if not isinstance(value, str):
        return ""
    return "".join(char for char in value.strip() if ord(char) >= 32)[:length]


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_login_branding():
    """Expose only site-configured public visual data on the login page."""
    result = {
        "brand_name": "",
        "brand_tagline": "",
        "logo_url": "",
        "logo_version": "",
        "media_url": "",
        "media_version": "",
        "media_kind": "",
        "accent_color": _DEFAULT_COLOR,
    }
    try:
        settings = frappe.get_cached_doc("Business Branding Settings")
    except frappe.DoesNotExistError:
        # During a rolling upgrade the old Single DocType may still exist.
        try:
            settings = frappe.get_cached_doc("Bisness Branding Settings")
        except frappe.DoesNotExistError:
            return result

    result["brand_name"] = _safe_label(settings.get("brand_name"), 80)
    result["brand_tagline"] = _safe_label(settings.get("brand_tagline"), 140)
    result["logo_url"], result["logo_version"] = _public_asset(
        settings.get("brand_logo"), _IMAGE_SUFFIXES
    )
    result["media_url"], result["media_version"] = _public_asset(
        settings.get("animation_file"), _IMAGE_SUFFIXES | _VIDEO_SUFFIXES
    )
    if result["media_url"]:
        suffix = PurePosixPath(unquote(urlsplit(result["media_url"]).path)).suffix.lower()
        result["media_kind"] = "video" if suffix in _VIDEO_SUFFIXES else "image"
    result["accent_color"] = _safe_color(settings.get("accent_color"))
    return result
