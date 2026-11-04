# Vira RFP Traceability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the Vira customer requirements a versioned, primary ERP project document with a separate machine-readable requirements graph beside the generated Graphify code graph.

**Architecture:** Customer RFP → stable requirement IDs and PDF section/page evidence → Mermaid and JSON business graph → README/AGENTS navigation. Do not alter generated Graphify files, deployment, or runtime.

**Tech Stack:** GitHub Markdown, YAML, Mermaid, JSON, Graphify (code-only).

**Spec:** `docs/requirements/VIRA_RFP.md` and source PDF SHA256 `acd665933df4fc029446e6d92147f7e1598d56321fa99733215e5ba366177440`.

## Global Constraints
- Only private `esi-ubuntu/ERP`, existing PR #1 branch.
- All implementation states default to `unverified`.
- Suggested acceptance and P0/P1 triage are clearly separate from RFP facts.
- No deployment, Actions run, source-submodule download, or change to generated `graphify-out/`.
- Keep repo's existing Graph-first policy; customer requirements are checked before code-impact work.

## Review Focus
- Missing or duplicate requirement IDs must fail validation.
- Sum of 14 user rows must be exactly 226; distinguish estimate from final licensing.
- Never mark ERPNext capability ready without source/runtime evidence.
- Preserve explicit Microsoft preference as an unresolved qualification gate.
- Do not write proposed graph dependencies as contractual obligations.

## Tasks
- [x] **Task 1 — Source trace:** register 59 granular requirements with RFP section/page, status, draft acceptance, and immutable IDs in YAML.
- [x] **Task 2 — Primary documents:** create human-readable RFP mapping, assumptions, risk gates and source provenance.
- [x] **Task 3 — Companion graph:** include all 59 requirements as machine nodes, domain edges, proposed dependencies and readable Mermaid views.
- [x] **Task 4 — Entry points:** link README, AGENTS and Graphify operating guide to the requirements source and graph.
- [x] **Task 5 — Verify remote:** read the committed files from GitHub and confirm IDs, paths and PR head; report any gap.

## Verification
- `requirements.yaml`: 59 unique IDs; every item has a domain, section and PDF page; all assessment statuses unverified.
- `requirements-graph.json`: every ID appears exactly once as a node; all edge endpoints are existing nodes.
- 14 listed user counts sum to 226.
- README and AGENTS links resolve inside the same branch.
- No automated Graphify build or CI run is part of this documentation-only task.
