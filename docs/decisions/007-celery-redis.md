# ADR-007: Celery and Redis for processing jobs

**Status:** accepted · **Date:** 2026-08-19

## Context

Asynchronous processing needs a job model with status tracking and retries, plus a way
to run the same code deterministically in tests without infrastructure.

## Decision

Use Celery over Redis for team deployments, with `CELERY_TASK_ALWAYS_EAGER` for local
development and tests.

## Consequences

- One job abstraction covers both modes; the workflow and its tests need no broker.
- `ProcessingJob` / `ProcessingRun` carry status, warnings, and errors.
- Redis becomes an operational dependency (and trust boundary) in team mode.
