# Customer requirement evidence (not product defaults)

These files capture **one customer's** request for proposal. They remain for audit and traceability:

- `VIRA_RFP.md`: paraphrased original RFP, including its source hash.
- `requirements.yaml`: 59 source-specific requirement IDs and unverified assessments.
- `../architecture/requirements-graph.md` / `.json`: source-specific business graph.

**Do not import this company hierarchy, the client name, user counts, bank details or RFP IDs into `bisness_core` as application defaults.** Other clients must have their own independent RFP/evidence records and site configuration. Rename or migrate historical IDs only with an explicit traceability decision.

Use `docs/architecture/product-core.md` for the reusable platform architecture. Documented requirements are not implemented functionality.
