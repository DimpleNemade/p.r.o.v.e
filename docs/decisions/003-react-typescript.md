# ADR-003: React and TypeScript investigator interface

**Status:** accepted · **Date:** 2026-08-19

## Context

The interface must support progressive disclosure (simple by default, technical detail
on demand), run in both a browser and a desktop shell, and be testable.

## Decision

Build the UI with React 18, TypeScript, and Vite; test with Vitest, Testing Library,
and Playwright. Use custom CSS (no Tailwind/shadcn in V0.1).

## Consequences

- One application serves both the browser and the Tauri shell.
- TypeScript catches API contract drift at build time.
- V0.1 ships a single-view workspace; `react-router` and `react-query` are declared but
  not yet used — an open decision (see [19](../19-phase-0-gap-analysis.md)).
