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

# Iran localization: pin to the commit tested by the successful v16 CI run.
# The branch HEAD must match; builds fail closed when upstream moves.
ARG IRAN_REF=main
ARG IRAN_SHA=60dc7b8b51f42a74ba65bee314922326788db59b

RUN bench get-app --branch "${HRMS_REF}" https://github.com/frappe/hrms.git \
    && test "$(git -C apps/hrms rev-parse HEAD)" = "${HRMS_SHA}" \
    && bench get-app --branch "${IRAN_REF}" https://github.com/bijanshdevops/erpnext_iran.git \
    && test "$(git -C apps/erpnext_iran rev-parse HEAD)" = "${IRAN_SHA}"

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
LABEL org.opencontainers.image.description="ERPNext + HRMS + Iranian localization + Bisness Core"

