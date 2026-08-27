# ADR-004: Tauri desktop shell

**Status:** accepted · **Date:** 2026-08-19

## Context

Some deployments will want a desktop application, but bundling a Python runtime and
granting broad native access in V0.1 would expand the trust boundary before it is
understood.

## Decision

Provide a Tauri 2 shell that hosts the same web UI, with narrow, explicit permissions
and no bundled backend.

## Consequences

- No filesystem plugin, no unrestricted native capability, no bundled Python.
- The browser app is the primary, supported target; the shell is optional.
- Building the shell needs Rust/Cargo and platform tools; it is currently unverified.
