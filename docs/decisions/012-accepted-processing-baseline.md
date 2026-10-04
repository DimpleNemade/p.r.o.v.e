# ADR-012: Explicit accepted processing baseline

Status: accepted, 2026-09-09

## Context

A newly calculated digest proves no acquisition authenticity and cannot silently become a
verified reference.

## Decision

Keep operator reference, every observation and accepted baseline separate. A missing
reference produces `baseline_pending`; acceptance needs actor/reason/time/limitations.
Every processing attempt compares against the immutable accepted value.

## Consequences

Unreferenced inputs require an extra human action and accurate limitation language.
Later mismatches retain both accepted and observed digests and block output.
