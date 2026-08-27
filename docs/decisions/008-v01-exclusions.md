# ADR-008: Exclude high-risk capabilities from V0.1

**Status:** accepted · **Date:** 2026-08-19

## Context

Mobile, cloud, memory, and network forensics, complete parser coverage, autonomous AI,
and graph storage are each large capabilities that require their own intended-use
definition, validation, threat modelling, and governance.

## Decision

Exclude them from V0.1. The first release delivers one narrow, end-to-end, provenance-
preserving workflow instead.

## Consequences

- The product must not imply unsupported capability; documentation and UI say what is
  and is not covered.
- Each excluded capability re-enters only as a separate scoped tranche with its own
  gate.
- Scope is defended by the change test in [01 Product constitution](../01-product-constitution.md).
