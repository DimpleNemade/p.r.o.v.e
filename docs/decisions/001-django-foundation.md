# ADR-001: Django as platform foundation

**Status:** accepted · **Date:** 2026-08-19

## Context

The platform needs authentication, sessions, an ORM with migrations, an admin surface,
and a custom user model from day one, on a stack shared with the processing worker.

## Decision

Use Django as the backend framework.

## Consequences

- Mature, batteries-included sessions, password hashing, CSRF middleware, ORM,
  migrations, and admin.
- A custom user model (`identity.User`) is defined before the first migration.
- The backend is Python-centric — accepted, because the worker and API share one
  ecosystem and one set of domain types.
