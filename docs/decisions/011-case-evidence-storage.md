# ADR-011: Case-relative evidence storage

Status: accepted, 2026-09-09

## Context

Absolute operator paths expose server files and do not express case authorization.

## Decision

Store a logical forward-slash locator and resolve it only below
`<EVIDENCE_ROOT>/<case UUID>`. Reject unsupported Windows/UNC/device/stream, traversal,
links/reparse points and non-regular files. Read one bounded immutable snapshot.

## Consequences

Legacy absolute paths need explicit relocation. Identity checks reduce but do not fully
eliminate concurrent filesystem modification; immutable storage remains preferable.
