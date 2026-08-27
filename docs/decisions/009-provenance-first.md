# ADR-009: Provenance as a first-class data model

**Status:** accepted · **Date:** 2026-08-19

## Context

Evidence, processing runs, artifacts, timeline events, findings, reports, and exports
all need durable, queryable links back to their sources. Relying on implicit foreign
keys would make traceability something the UI reconstructs rather than something the
system guarantees.

## Decision

Model provenance explicitly as `investigations.ProvenanceLink`
(`source_evidence` → `artifact`, with `relationship` and `rationale`), created by the
processing worker and exposed through the API with no update/delete route.

## Consequences

- The API, UI, and a future export manifest can make traceability explicit and testable
  (e.g. "find findings whose support chain does not reach verified evidence").
- Missing provenance is a visible review state, never an inferred relationship.
- The `(source_evidence, artifact, relationship)` triple is unique.
