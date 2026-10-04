# Changelog

## Unreleased

### Phase 3 — evidence integrity and reproducible handoff

- Enforced case-relative evidence storage, persistent hash observations and explicit
  acceptance for locally calculated baselines.
- Added centralized account-and-membership authorization, relationship validation,
  immutable review fields and independent finding revisions.
- Isolated processing in a dedicated child process; the `team` profile requires a Linux
  `bwrap` sandbox (no network, dropped capabilities, resource limits) with no
  unsandboxed fallback.
- Added database-backed job idempotency, atomic claiming/output commits, intentional
  re-examinations, publication recovery and bounded worker execution.
- Added honest timestamp semantics, a canonical per-case audit chain with legacy
  checkpoint, real deterministic export packages and an offline hostile-archive verifier.
- Isolated browser/test data and ports, made demo seeding non-destructive, and added
  PostgreSQL/Redis/Celery CI integration configuration.
- Upgraded to Django 5.2.17 LTS, DRF 3.16.1 and Vitest 5.0.0; added real Mermaid rendering.
- Fixed root-level backend test discovery (`manage.py` now runs from its own directory
  regardless of invocation path) and aligned `pytest` to collect the same test suite.
- Renamed `docs/20-phase-3-implementation-verification.md` to
  `docs/21-phase-3-implementation-verification.md` so it does not share a number with
  `docs/20-step-2-core-investigator-workflow.md`.

### Step 2 — core investigator workflow

- Added versioned `/api/v1` routes with `/api/` compatibility aliases.
- Added case, evidence, artifact, timeline, provenance, finding, report, and audit detail flows with explicit serializers and error codes.
- Enforced verify-before-process and recorded verification, processing, finding/support, report, login, and logout audit events.
- Expanded the idempotent synthetic seed to three evidence fixtures, three processing runs, artifacts, timeline events, provenance links, a finding, support, report, and audit history.
- Added authenticated browser coverage for the complete investigator journey and dedicated detail panels in the web workspace.
- Added Step 2 architecture notes and Mermaid workflow, sequence, provenance, support, reporting, and permission diagrams.
- Renamed `docs/19-step-2-core-investigator-workflow.md` to `docs/20-step-2-core-investigator-workflow.md` so no two documents share the `19-` prefix.

## 0.1.1 - 2026-08-27

- Renamed the project to P.R.O.V.E (Provenance, Register, Observe, Verify, Examine).
- Initialised the Git repository with history grouped by component.
- Updated the API schema title, web and desktop package names, and the Tauri bundle identity to match.
- Added `.gitattributes` for line-ending normalisation.
- Rewrote the README as a full project introduction: problem statement, origin,
  use cases, landscape positioning, cross-platform setup, and embedded
  architecture and workflow Mermaid diagrams.
- Recorded ownership in `LICENSE`.

## 0.1.0 - 2026-08-19

- Created provenance-first Django/DRF API scaffold.
- Added React investigator workspace and Tauri shell placeholder.
- Added synthetic forensic worker, documentation, diagrams, and verification scaffolding.
- Added root-safe backend test discovery, CSRF-protected login flow, environment checking, and Phase 1 verification documentation.
