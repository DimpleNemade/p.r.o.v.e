# ADR-010: Explicit, versioned core investigator workflow

**Status:** accepted  
**Date:** 2026-09-02

## Context

The Phase 1 scaffold had the domain models and a small happy-path API, but an investigator
could not reliably move from a case to a specific evidence detail, derived artifact,
provenance chain, supported finding, report snapshot, and audit history. Compatibility with
the existing `/api/` clients also mattered.

## Decision

Implement the Step 2 journey as explicit, case-authorized detail endpoints and routed web
views. Publish `/api/v1/` as the canonical prefix while retaining `/api/` aliases. Enforce
verification before processing, serialize only safe structured data, and record material
actions in append-only audit/custody/provenance records. Use synthetic, idempotent seed data
to exercise at least two verified evidence items and the complete downstream chain.

## Consequences

Investigators can follow a reproducible navigation path and reviewers can inspect the
source, method, support, and limitations behind a draft report. API clients get explicit
error codes and stable versioning. The UI and tests are more involved, and the current
report/export remains intentionally non-operational until formal validation and deployment
controls are designed.
