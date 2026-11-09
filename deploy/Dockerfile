# Build a local ERPNext v16 image with vetted third-party apps and our own app.
# The base tag is fixed; pin a registry digest before a production release.
ARG ERPNEXT_VERSION=v16.53.0
FROM frappe/erpnext:${ERPNEXT_VERSION} AS runtime

# The official runtime image intentionally lacks many build dependencies.
# Use the matching upstream v16 build stage for third-party app compilation.
FROM frappe/build:version-16 AS builder
USER frappe
COPY --from=runtime --chown=frappe:0 /home/frappe/frappe-bench /home/frappe/frappe-bench
WORKDIR /home/frappe/frappe-bench

# Official HRMS v16.53.0 tag resolves to this reviewed Git commit.
ARG HRMS_REF=v16.53.0
ARG HRMS_SHA=b12d935b99c1434618845fdd9f3a3d340b5a3aed

# Preserve the previously deployed Iranian localization revision. The
# upstream main branch has changed; checkout the reviewed Git object BEFORE
# installing or building any source from that repository.
ARG IRAN_SHA=7de4bf520a459d2183086031c9bbad0bd99995ef

RUN bench get-app --branch "${HRMS_REF}" https://github.com/frappe/hrms.git \
    && test "$(git -C apps/hrms rev-parse HEAD)" = "${HRMS_SHA}"

RUN git clone --quiet --no-checkout https://github.com/bijanshdevops/erpnext_iran.git apps/erpnext_iran \
    && git -C apps/erpnext_iran checkout --quiet --detach "${IRAN_SHA}" \
    && test "$(git -C apps/erpnext_iran rev-parse HEAD)" = "${IRAN_SHA}" \
    && ./env/bin/pip install --no-cache-dir -e apps/erpnext_iran \
    && bench build --app erpnext_iran

# Version 16-compatible, reviewed upstream revisions.
# Frappe CRM stable v1.x uses main, Frappe Insights v3 supports Frappe 16.
ARG CRM_REF=main
ARG CRM_SHA=638bf3db23e7142870819a213368e028866b79b1
ARG INSIGHTS_REF=version-3
ARG INSIGHTS_SHA=c7dc954d8275756deb5ad24f7c35c3f3c2ca1a6c

RUN bench get-app --branch "${CRM_REF}" https://github.com/frappe/crm.git \
    && test "$(git -C apps/crm rev-parse HEAD)" = "${CRM_SHA}" \
    && bench get-app --branch "${INSIGHTS_REF}" https://github.com/frappe/insights.git \
    && test "$(git -C apps/insights rev-parse HEAD)" = "${INSIGHTS_SHA}"

# Frappe Wiki (v16-compatible development branch).
# Telephony and Helpdesk are deliberately NOT included per operator request.
ARG WIKI_SHA=2abd7795b4e6069a05a45ac04226068ef831feac

# Wiki's Vite socket client imports socketio_port as a named JSON export
# during its automatic bench get-app asset build. Set the same value used by
# our production configurator (it will reapply this setting at runtime).
RUN bench set-config -gp socketio_port 9000

# Lock Wiki to the exact tested commit as well; its develop branch moves.
# Install Python and JS dependencies only after the verified checkout.
RUN git clone --quiet --no-checkout https://github.com/frappe/wiki.git apps/wiki \
    && git -C apps/wiki checkout --quiet --detach "${WIKI_SHA}" \
    && test "$(git -C apps/wiki rev-parse HEAD)" = "${WIKI_SHA}" \
    && ./env/bin/pip install --no-cache-dir -e apps/wiki \
    && (cd apps/wiki && yarn install --check-files) \
    && bench build --app wiki

COPY --chown=frappe:0 apps/bisness_core /home/frappe/frappe-bench/apps/bisness_core

RUN ./env/bin/pip install --no-cache-dir -e apps/bisness_core \
    && bench build \
    && cp -r sites/assets/. assets/ \
    && rm -rf sites/assets

# Preserve the official runtime entrypoint, web-server utilities and volumes.
FROM runtime AS final
COPY --from=builder --chown=frappe:0 /home/frappe/frappe-bench /home/frappe/frappe-bench
USER frappe
WORKDIR /home/frappe/frappe-bench

LABEL org.opencontainers.image.title="Generic ERPNext business stack"
LABEL org.opencontainers.image.description="ERPNext + HRMS + Iranian localization + Bisness Core + CRM + Insights + Wiki"

