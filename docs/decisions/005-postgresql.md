# ADR-005: PostgreSQL as shared team database

**Status:** accepted · **Date:** 2026-08-19

## Context

Team use needs real constraints, indexing, JSON metadata support, and operational
maturity (backups, concurrent access, migrations at scale).

## Decision

PostgreSQL is the intended shared database. SQLite is retained only as a local
development fallback.

## Consequences

- `DATABASE_URL` selects PostgreSQL; absent it, development uses `apps/api/db.sqlite3`.
- Models use `JSONField`, UUID keys, unique constraints, and check constraints that both
  engines support.
- PostgreSQL-backed behaviour is unverified until an infrastructure run exercises it.
