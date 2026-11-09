"""Application metadata. Keep all customer data out of the codebase."""

app_name = "bisness_core"
app_title = "Bisness Core"
app_publisher = "ERP Platform Contributors"
app_description = "Reusable ERPNext business extensions"
app_icon = "octicon octicon-organization"
app_color = "blue"
# App distribution license is pending a separate commercial/legal decision.
app_license = "License pending"

# These apps must be installed before bisness_core.
required_apps = ["erpnext", "hrms", "erpnext_iran"]

# Apply the product's login-only visual layer to Frappe's native website login.
# Do not replace frappe/www/login.html: that page owns the supported login,
# reset-password, LDAP and social-authentication workflows.
web_include_css = ["/assets/bisness_core/css/login-theme.css"]
web_include_js = ["/assets/bisness_core/js/login-branding.js"]

