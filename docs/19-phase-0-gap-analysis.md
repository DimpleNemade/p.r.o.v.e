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
| Single hash service | Gap | Verification logic is duplicated in the endpoint and the worker task. Extract one service. |
| Audit / provenance complete | Mostly | Append-only, written on every material action. Add a check that every artifact has a provenance link and expose "orphans". |
| Manifest / reproducibility package | Gap | Export is a placeholder. Build the manifest (identifiers, hashes, processor versions, parameters, limitations). |
| Versions & configuration recorded per run | Partial | `ProcessingRun` stores processor name+version; it does not yet capture dependency versions, parameters, or environment. |
| Hostile-file isolation demonstrated | Missing | Worker runs in-process with no sandbox, resource limits, or network restriction. Containerise with dropped capabilities and no egress. |
| Reproducible environment | Partial | Deps pinned; no lockfile-based container image or documented clean-room rebuild for the API. |
| No unauthorised network path | Done | No external calls; CORS/CSRF allowlists explicit. |
| Validation master plan approved | Missing | Create A07; define risk classes, corpus strategy, and acceptance criteria. |

## Engineering backlog (independent of gates)

| Priority | Item |
| --- | --- |
| High | `Model.objects.get()` → `404` (currently `500`) across `cases/views.py` detail routes. |
| High | Real frontend tests (render the app; cover login, a protected panel, an error state) and an authenticated E2E path. |
| High | Consolidate verification into one hash service. |
| Medium | Endpoints for `CaseParticipant`, `TimelineEvent`, `InvestigatorNote`, `Bookmark`. |
| Medium | Finding review workflow (reviewer role, `review_status` transitions, `reviewer_comments`). |
| Medium | Decide `react-router` + `react-query` in or out; remove if unused. |
| Low | Replace `from .serializers import *`; split the single `App.tsx`. |
| Low | Implement `packages/api-client` or drop it. |

## Recommended sequence

1. **Freeze feature work.** Treat the current scaffold as the roadmap's "workflow
   prototype" deliverable.
2. **Write the G0 artefacts:** constitution (A01), requirements catalogue (A02),
   standards register (A03), risk register (A12).
3. **Harden the foundation:** one hash service, worker isolation, `404` handling,
   per-run configuration capture, real tests.
4. **Design validation:** validation master plan (A07) and the first synthetic
   ground-truth scenario.
5. **Re-baseline the timeline** against actual headcount and secure an independent
   reviewer; if neither is available, cap the stated ambition at "controlled alpha".

Related: [17 Phase 1 verification report](17-phase-1-verification-report.md) ·
[12 Validation & testing](12-validation-and-testing.md).
