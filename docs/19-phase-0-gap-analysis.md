# Phase 0 gap analysis

Where the V0.1 scaffold stands against the programme roadmap's early gates — **G0
(constitution)** and **G1 (assurance foundation)** — and what closing them requires.

> This is an engineering self-assessment, not an approved gate decision.

## Summary

The scaffold is roughly at **pre-G0, with an early-G1 skeleton in code**. It moved ahead
on workflow UI and CRUD, and is behind on the constitution and assurance paperwork that
the roadmap wants settled *first*. The strongest parts (provenance model, append-only
ledger, blocking hash mismatch) are genuine G1 building blocks; the weakest are
independent-review capacity, worker isolation, and validation planning.

**Step 2 update (merged).** The workflow-hygiene backlog is closed: one SHA-256 service
([`evidence/services.py`](../apps/api/evidence/services.py)), `404` handling on every
detail route, endpoints for participants / timeline / notes / bookmarks, a versioned
finding-edit path, real frontend and end-to-end tests, and verify-before-process. The
open G1 items are now structural — worker isolation, a reproducibility manifest, per-run
configuration capture, a validation master plan, and a ground-truth corpus. See
[20 Step 2 core workflow](20-step-2-core-investigator-workflow.md).

## G0 — constitution

| Exit criterion | Status | Gap / action |
| --- | --- | --- |
| Intended uses and non-uses approved | Partial | Scope is written ([02](02-v0.1-scope.md)) but not ratified as an approved artefact (A01). |
| Initial scenario defined | Missing | Roadmap targets a Windows USB/file-activity scenario; V0.1 processes only synthetic files. Write the scenario narrative. |
| Jurisdiction & standards baseline | Partial | Programme doc names E&W / FSR Code v2; the repo does not yet carry a standards/applicability register (A03). |
| Users & roles | Done | Six roles modelled; permission split enforced for `administrator` vs participant. |
| Claims discipline | Done | "Not court-ready / not validated" stated in README, LICENSE, and [01](01-product-constitution.md). |
| P0 principles recorded | Done | [01 Product constitution](01-product-constitution.md). |
| Decision rights & success measures | Missing | No named gate owner, review authority, or measurable success thresholds yet. |
| Risk register | Missing | Create A12 with severity/owner/mitigation. |

## G1 — assurance foundation

| Exit criterion | Status | Gap / action |
| --- | --- | --- |
| Original evidence unchanged | Done | Read-only access; no modify/delete route; worker never opens evidence for writing. |
| Hashes verified, mismatch blocking | Done | `verify` endpoint + worker both stop on mismatch; states recorded in custody + audit. |
| Single hash service | Done (Step 2) | `evidence/services.py` is the one SHA-256 service used by both the verify endpoint and the worker task. |
| Audit / provenance complete | Mostly | Append-only, written on every material action. Add a check that every artifact has a provenance link and expose "orphans". |
| Manifest / reproducibility package | Gap | Export is still a placeholder on `main`. A deterministic package plus offline verifier is in development, not yet merged. |
| Versions & configuration recorded per run | Partial | `ProcessingRun` stores processor name+version; dependency versions, parameters, and environment capture are in development, not yet merged. |
| Hostile-file isolation demonstrated | Missing | Worker runs in-process with no sandbox, resource limits, or network restriction. Containerise with dropped capabilities and no egress. |
| Reproducible environment | Partial | Deps pinned; no lockfile-based container image or documented clean-room rebuild for the API. |
| No unauthorised network path | Done | No external calls; CORS/CSRF allowlists explicit. |
| Validation master plan approved | Missing | Create A07; define risk classes, corpus strategy, and acceptance criteria. |

## Engineering backlog (independent of gates)

Tracked against the code on `main`.

| Priority | Item | Status |
| --- | --- | --- |
| High | `Model.objects.get()` → `404` on `cases/views.py` detail routes | Done (Step 2) — `get_object_or_404` throughout |
| High | Real frontend tests and an authenticated E2E path | Done (Step 2) — Vitest specs plus a full Playwright journey |
| High | Consolidate verification into one hash service | Done (Step 2) — `evidence/services.py` |
| Medium | Endpoints for `CaseParticipant`, `TimelineEvent`, `InvestigatorNote`, `Bookmark` | Done (Step 2) |
| Medium | Finding review workflow | Partial (Step 2) — versioned edit path and `finding_basis`; full revision / independent-review state machine still open |
| Medium | Decide `react-router` + `react-query` in or out | Done (Step 2) — both adopted and in use |
| Low | Replace `from .serializers import *`; split the single `App.tsx` | `import *` removed (Step 2); `App.tsx` is routed but still one file |
| Low | Implement `packages/api-client` or drop it | Open |

## Recommended sequence

1. **Freeze feature work.** Treat the current scaffold as the roadmap's "workflow
   prototype" deliverable.
2. **Write the G0 artefacts:** constitution (A01), requirements catalogue (A02),
   standards register (A03), risk register (A12).
3. **Harden the foundation:** worker isolation, per-run configuration capture, and the
   reproducibility manifest. (One hash service, `404` handling, and real tests landed in
   Step 2.)
4. **Design validation:** validation master plan (A07) and the first synthetic
   ground-truth scenario.
5. **Re-baseline the timeline** against actual headcount and secure an independent
   reviewer; if neither is available, cap the stated ambition at "controlled alpha".

Related: [17 Phase 1 verification report](17-phase-1-verification-report.md) ·
[20 Step 2 core workflow](20-step-2-core-investigator-workflow.md) ·
[12 Validation & testing](12-validation-and-testing.md).
