# Phase 0 gap analysis

Where the V0.1 scaffold stands against the programme roadmap's early gates — **G0
(constitution)** and **G1 (assurance foundation)** — and what closing them requires.

> This is an engineering self-assessment, not an approved gate decision.

## Summary

The scaffold is roughly at **pre-G0, with G1 substantially built in code**. It moved
ahead on workflow UI and CRUD, and is still behind on the constitution and assurance
paperwork that the roadmap wants settled *first*. The G1 building blocks — provenance
model, append-only ledger, blocking hash mismatch, worker isolation, the reproducibility
manifest — are now in place; the weakest areas are G0 governance paperwork, independent
review capacity, and formal validation planning.

**Step 2 update (merged).** The workflow-hygiene backlog is closed: one SHA-256 service
([`evidence/services.py`](../apps/api/evidence/services.py)), `404` handling on every
detail route, endpoints for participants / timeline / notes / bookmarks, a versioned
finding-edit path, real frontend and end-to-end tests, and verify-before-process. See
[20 Step 2 core workflow](20-step-2-core-investigator-workflow.md).

**Phase 3 update (merged).** The structural G1 gaps are closed: a fail-closed,
case-relative evidence storage boundary with explicit baseline acceptance; a
hash-chained, tamper-evident audit ledger with a legacy checkpoint and an offline
verifier; a role × case-membership capability matrix with independent finding review
(no role, including administrator, can approve its own work); isolated, resource-limited
processing in a dedicated child process (`team` profile requires a Linux `bwrap`
sandbox — no network, dropped capabilities, CPU/memory/file/FD limits); per-run
configuration and dependency capture; and a deterministic, offline-verifiable export
package. Remaining G1 gaps are a validation master plan and a ground-truth corpus — see
[21 Phase 3 implementation verification](21-phase-3-implementation-verification.md).

## G0 — constitution

| Exit criterion | Status | Gap / action |
| --- | --- | --- |
| Intended uses and non-uses approved | Partial | Scope is written ([02](02-v0.1-scope.md)) but not ratified as an approved artefact (A01). |
| Initial scenario defined | Missing | Roadmap targets a Windows USB/file-activity scenario; V0.1 processes only synthetic files. Write the scenario narrative. |
| Jurisdiction & standards baseline | Partial | Programme doc names E&W / FSR Code v2; the repo does not yet carry a standards/applicability register (A03). |
| Users & roles | Done | Six roles modelled; a role × case-membership capability matrix is enforced (`cases/permissions.py`). |
| Claims discipline | Done | "Not court-ready / not validated" stated in README, LICENSE, and [01](01-product-constitution.md). |
| P0 principles recorded | Done | [01 Product constitution](01-product-constitution.md). |
| Decision rights & success measures | Missing | No named gate owner, review authority, or measurable success thresholds yet. |
| Risk register | Partial | [`docs/phase3/risk-register.md`](phase3/risk-register.md) covers engineering risk; not yet the roadmap's formal A12 artefact. |

## G1 — assurance foundation

| Exit criterion | Status | Gap / action |
| --- | --- | --- |
| Original evidence unchanged | Done | Read-only, case-relative storage boundary; no modify/delete route; the worker never opens evidence for writing. |
| Hashes verified, mismatch blocking | Done | Verify endpoint and worker task share one service; mismatch and unreadable states are blocking and recorded in custody + audit. |
| Single hash service | Done (Step 2) | `evidence/services.py` is the one SHA-256 service used by both the verify endpoint and the worker task. |
| Audit / provenance complete | Mostly | Append-only and hash-chained, written on every material action. An explicit "every artifact has a provenance link" orphan check is still open. |
| Manifest / reproducibility package | Implemented in Phase 3 | Canonical snapshot, deterministic ZIP, create/status/download and an offline verifier. |
| Versions & configuration recorded per run | Implemented in Phase 3 | Run records include input/output digests, normalized parameters, processor/schema and relevant dependency versions. |
| Hostile-file isolation demonstrated | Implemented in Phase 3, bare-host verified | Processing runs in a dedicated child process; the `team` profile requires a Linux `bwrap` sandbox (no network, dropped capabilities, resource limits) with no unsandboxed fallback. CI's `team-integration` job exercises this directly on the runner and passes. Running bwrap *inside* the hardened `worker` container in `docker-compose.team.yml` is not yet verified — see [phase3/operations.md](phase3/operations.md) and the tracking issue. |
| Reproducible environment | Partial | Deps pinned; no lockfile-based container image or documented clean-room rebuild for the API itself. |
| No unauthorised network path | Done | No external calls; CORS/CSRF allowlists explicit; the processing sandbox has no network namespace. |
| Validation master plan approved | Missing | Create A07; define risk classes, corpus strategy, and acceptance criteria. |

## Engineering backlog (independent of gates)

Tracked against the code on `main`.

| Priority | Item | Status |
| --- | --- | --- |
| High | `Model.objects.get()` → `404` on `cases/views.py` detail routes | Done (Step 2) — `get_object_or_404` throughout |
| High | Real frontend tests and an authenticated E2E path | Done (Step 2) — Vitest specs plus a full Playwright journey |
| High | Consolidate verification into one hash service | Done (Step 2) — `evidence/services.py` |
| Medium | Endpoints for `CaseParticipant`, `TimelineEvent`, `InvestigatorNote`, `Bookmark` | Done (Step 2) |
| Medium | Finding review workflow | Done (Phase 3) — `FindingRevision` / `ReviewDecision` state machine with independent review enforced |
| Medium | Decide `react-router` + `react-query` in or out | Done (Step 2) — both adopted and in use |
| Low | Replace `from .serializers import *`; split the single `App.tsx` | `import *` removed (Step 2); `App.tsx` is routed but still one file |
| Low | Implement `packages/api-client` or drop it | Open |

## Recommended sequence

1. **Freeze feature work.** Treat the current scaffold as the roadmap's "workflow
   prototype" deliverable. *(Superseded in practice by Step 2 and Phase 3; revisit once
   this backlog is this short again.)*
2. **Write the G0 artefacts:** constitution (A01), requirements catalogue (A02),
   standards register (A03), decision rights and success measures — still open, and now
   the critical path to G0.
3. ~~Harden the foundation: worker isolation, per-run configuration capture, and the
   reproducibility manifest.~~ **Done — delivered in Phase 3.**
4. **Design validation:** a validation master plan (A07) and the first synthetic
   ground-truth scenario — still open; the next engineering priority.
5. **Re-baseline the timeline** against actual headcount and secure an independent
   reviewer; if neither is available, cap the stated ambition at "controlled alpha".

Related: [17 Phase 1 verification report](17-phase-1-verification-report.md) ·
[20 Step 2 core workflow](20-step-2-core-investigator-workflow.md) ·
[21 Phase 3 implementation verification](21-phase-3-implementation-verification.md) ·
[12 Validation & testing](12-validation-and-testing.md).
