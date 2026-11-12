# Configurable ERP login branding

Each site has **Business Branding Settings**. The visible label is spelled
"Business"; the stable Python/Frappe application identifier stays
`bisness_core` to avoid breaking database names, routes and installed sites.

1. Sign in as a **System Manager** and open the **Business Settings**
   workspace from the Desk. Choose the **Business Branding Settings** shortcut
   or the **Login Branding** sidebar entry (no search required).
2. Set **Brand Name**, **Brand Tagline**, **Brand Logo** and **Accent Color**.
3. For the large visual panel use **Login Image or Animation**. Supported:
   PNG/JPEG/WebP/GIF/SVG/AVIF, MP4 and WebM. Video loops muted and inline;
   reduced-motion visitors receive controls rather than autoplay.
4. **Both files must be PUBLIC.** For a file uploaded with Frappe's Attach
   controls, verify that it is not marked `is_private=1`; private uploads,
   external URLs, unsupported formats and non-file URLs are intentionally
   ignored by the public login page.
5. **Save**, open `/login` in a new private window or refresh. The client
   waits for Frappe's login container and only swaps the hero after the new
   image/video loads. The public branding API emits an asset revision to
   invalidate the browser cache on file changes. Clear **Login Image or
   Animation** to restore the built-in animated orbit.
6. If a file still fails to display, inspect whether it resolves under
   `/files/`, whether the `File` record is public, and the browser's
   network errors. The previous default graphic remains if a file is missing.

The Frappe native login, reset-password, LDAP and social-auth handlers remain
unchanged. A guest API reveals only public display data; it checks a public
Frappe `File` record for uploads, not just URL text.

### Migration

An upgrade includes a **pre-model-sync patch** that renames the previous
`Bisness Branding Settings` Single DocType to
`Business Branding Settings` while preserving brand fields and their
existing single-value contents. Never rename the underlying app.

New settings and the workspace require a controlled `bench migrate` on a
staging copy first. Uploaded file bytes remain in per-site file storage and
are never embedded in Git. Production upgrades need the site's separate
backup/approval/rollback process.
