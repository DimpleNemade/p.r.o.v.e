# ADR-005: PostgreSQL as shared team database

Status: accepted.

PostgreSQL is the intended shared database for constraints, indexing, JSON metadata, and operational maturity. SQLite is retained only as a local fallback when team infrastructure is unavailable.
