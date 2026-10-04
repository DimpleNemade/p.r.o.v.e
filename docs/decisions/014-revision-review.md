# ADR-014: Immutable finding revisions and independent review

Status: accepted, 2026-09-09

## Context

Mutable finding fields can inherit approval after their text or support changes.

## Decision

Submission freezes text, support and provenance in a hashed revision. Only a different
authorized account may start/decide review. Version checks prevent concurrent overwrite;
withdrawal and supersession require reasons and retain approved revisions.

## Consequences

Report snapshots cite exact approved revisions. Administrators cannot self-approve through
normal application behavior.
