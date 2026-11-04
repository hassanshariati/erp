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
