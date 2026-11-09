# Configurable ERP login branding

Each installed ERP site has its own settings. No customer name, logo or media URL is stored in product code.

1. Log in as a **System Manager**.
2. In the ERP Desk search bar, open **Bisness Branding Settings**.
3. Set **Brand Name**, **Brand Tagline**, **Brand Logo**, and **Accent Color**.
4. Optionally upload an **Animation File**. Accepted files: animated GIF/WebP/SVG, MP4 and WebM; PNG/JPEG also work as static replacements.
5. Make both attachments **public**; private file URLs are intentionally ignored on the public login page.
6. Save and refresh `/login`. Clear **Animation File** to restore the built-in animated orbit.

The `bisness_core` guest endpoint returns only public display data. It rejects private uploads, external URLs, unsupported extensions and invalid colors. The native Frappe login form and authentication handlers are unchanged.

The existing deployment image build includes the browser assets. New settings require the existing site upgrade to run `bench migrate` (already part of the repo's controlled production upgrade script). The upload content remains in the site's `files` storage and is not committed to Git.
