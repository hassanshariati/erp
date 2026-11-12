"""Application metadata. Keep all customer data out of the codebase."""

app_name = "bisness_core"
app_title = "Business Core"
app_publisher = "ERP Platform Contributors"
app_description = "Reusable ERPNext business extensions"
app_icon = "octicon octicon-organization"
app_color = "blue"
app_logo_url = "/assets/bisness_core/images/login-mark.svg"
app_home = "/desk/business-settings"

# Frappe v16 does not automatically show an installed custom app in the Apps
# desktop. The app switcher requires this explicit registration. Preserve the
# Python package name bisness_core for existing site data and patches.
add_to_apps_screen = [
    {
        "name": app_name,
        "logo": app_logo_url,
        "title": app_title,
        "route": app_home,
        "has_permission": "bisness_core.api.navigation.check_app_permission",
        "sequence_id": 30,
    }
]
# App distribution license is pending a separate commercial/legal decision.
app_license = "License pending"

# These apps must be installed before bisness_core.
required_apps = ["erpnext", "hrms", "erpnext_iran"]

# Apply the product's login-only visual layer to Frappe's native website login.
# Do not replace frappe/www/login.html: that page owns the supported login,
# reset-password, LDAP and social-authentication workflows.
web_include_css = ["/assets/bisness_core/css/login-theme.css"]
web_include_js = ["/assets/bisness_core/js/login-branding.js"]

