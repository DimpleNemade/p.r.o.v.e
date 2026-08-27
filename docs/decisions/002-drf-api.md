# ADR-002: Django REST Framework as API layer

**Status:** accepted · **Date:** 2026-08-19

## Context

The browser and desktop clients need a documented HTTP API with explicit
serialization, permission checks close to the domain models, and testability.

## Decision

Use Django REST Framework, with drf-spectacular for the OpenAPI schema.

## Consequences

- Explicit serializers and per-view permission classes; case authorization lives next
  to the models it protects.
- `APIClient`-based tests exercise auth, isolation, and the provenance path.
- Schema at `/api/schema/`, Swagger UI at `/api/docs/`.
- Function endpoints stay thin; most routes are `APIView` subclasses.
