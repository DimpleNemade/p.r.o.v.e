# ADR-006: Separate Python forensic worker

**Status:** accepted · **Date:** 2026-08-19

## Context

Processing handles untrusted evidence and will grow to include parser adapters. Running
it inside the request path would couple its failure modes, resource use, and future
sandboxing needs to the API.

## Decision

Keep processing in a separate worker with a small, explicit interface
(`services/forensic-worker/`), invoked as a Celery task from the API.

## Consequences

- Hashing and future parsers can scale, fail, and be governed independently.
- The worker writes structured results and provenance back through the API; it never
  writes original evidence and never logs raw contents.
- Isolation hardening (container, dropped capabilities, no network) is still to be
  implemented — see [19](../19-phase-0-gap-analysis.md).
