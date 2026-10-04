# ADR-015: Canonical audit chain and deterministic handoff

Status: accepted, 2026-09-09

## Context

Append-only routes alone do not reveal database edits, and delivery metadata makes whole
manifests unstable or recursive.

## Decision

Use versioned canonical event hashes, per-case sequence and custody/provenance bindings.
Capture an allowlisted case snapshot at an audit cutoff; hash canonical content and place
it in a deterministic bounded archive. Record export/download outside the cutoff.

## Consequences

Offline checks prove package consistency, not author identity. Local chains need separately
retained checkpoints to detect tail deletion and cannot defeat a rewriting administrator.
