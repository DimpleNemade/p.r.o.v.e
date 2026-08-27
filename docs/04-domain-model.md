# Domain model

The model is split by capability: identity, cases, evidence, processing, investigations, reporting, and audit. Stable UUIDs, timestamps, case relationships, indexes, constraints, and explicit deletion behavior are defined in Django models. Evidence, custody, provenance, audit, processing runs, artifacts, timeline events, findings, and reports are linked without copying raw evidence contents.

```mermaid
erDiagram
  USER ||--o{ CASE_PARTICIPANT : joins
  CASE ||--o{ CASE_PARTICIPANT : has
  CASE ||--o{ EVIDENCE_ITEM : contains
  EVIDENCE_ITEM ||--o{ ARTIFACT : derives
  PROCESSING_RUN ||--o{ ARTIFACT : creates
  ARTIFACT ||--o{ PROVENANCE_LINK : supports
  FINDING ||--o{ FINDING_SUPPORT : cites
  ARTIFACT ||--o{ FINDING_SUPPORT : supports
  CASE ||--o{ AUDIT_EVENT : records
