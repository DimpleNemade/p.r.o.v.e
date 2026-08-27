# Provenance and chain of custody

Custody events record who performed an evidence action and when. Provenance links connect source evidence to derived artifacts. The API exposes append operations and does not provide ordinary update/delete endpoints for these records. Missing provenance is a review state, not an inferred relationship.

```mermaid
flowchart LR
  E[Registered evidence + hash] --> R[Processing run]
  R --> A[Normalized artifact]
  A --> T[Timeline event]
  A --> F[Finding support]
  F --> P[Report statement]
  E -. custody events .-> C[Append-only custody ledger]
