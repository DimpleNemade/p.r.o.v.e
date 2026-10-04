# ADR-013: Database-backed processing identity and short transactions

Status: accepted, 2026-09-09

## Context

Broker delivery is at least once. An application `exists` check does not prevent duplicate
commits or distinguish deliberate re-examination.

## Decision

Constrain request keys, fingerprint inputs/method/schema, atomically claim a job, process
outside locks, and atomically commit all successful outputs. A rerun binds prior job,
reason and separate idempotency key. Publish only after commit and recover visibly.

## Consequences

Failed/interrupted attempts remain auditable. Team concurrency and real broker behavior
must pass the PostgreSQL/Redis/Celery integration gate.
