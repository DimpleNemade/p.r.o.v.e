# Programme overview

## Purpose

P.R.O.V.E is a **provenance-first digital forensic investigation platform**. It carries an
investigation from registered evidence through verification, processing, review, and
reporting in one workspace, and keeps every derived record — artifact, timeline event,
finding, report statement, export — linked to the evidence it came from, the processing
that produced it, and the examiner who decided about it.

V0.1 is a **foundation**, not a finished suite. The workflow, data model, API, web
interface, and worker boundary exist and are exercised by tests. Deep parsers,
acquisition integrations, and formal validation do not. See [V0.1 scope](02-v0.1-scope.md).

## Who it is for

| Stakeholder | What they get from V0.1 |
| --- | --- |
| Investigator | one connected workspace for the evidence-to-finding loop |
| Supervisor | case participants and permission levels |
| Reviewer / QA | a path from any finding back to its source and processing run |
| Auditor | an append-only record of every material action |
| Engineer | a readable, testable base with documented boundaries |

## What "success" means

Each important output can be followed back to registered source evidence, and an
examiner — not the automation — remains responsible for interpretation and conclusions.
Concretely, for V0.1:

- a hash mismatch is **blocking and visible**, never silent;
- observations, normalized interpretations, machine suggestions, and examiner
  conclusions are represented as **distinct states**;
- custody, provenance, and audit records are **append-only** through the application.

## Document map

| Area | Documents |
| --- | --- |
| Direction & scope | [01 Product constitution](01-product-constitution.md) · [02 V0.1 scope](02-v0.1-scope.md) |
| Design | [03 System architecture](03-system-architecture.md) · [04 Domain model](04-domain-model.md) · [ADRs](decisions/README.md) |
| Evidence & provenance | [05 Evidence lifecycle](05-evidence-lifecycle.md) · [06 Provenance & chain of custody](06-provenance-and-chain-of-custody.md) |
| Access & processing | [07 Authentication & authorization](07-authentication-and-authorization.md) · [08 Processing jobs](08-processing-jobs.md) |
| Interface | [09 API contract](09-api-contract.md) · [15 User workflows](15-user-workflows.md) |
| Assurance | [10 Security threat model](10-security-threat-model.md) · [11 Data protection & privacy](11-data-protection-and-privacy.md) · [12 Validation & testing](12-validation-and-testing.md) · [14 AI governance boundary](14-ai-governance-boundary.md) |
| Operations | [13 Deployment & operations](13-deployment-and-operations.md) · [18 Environment & toolchain](18-environment-and-toolchain.md) |
| Reference | [16 Glossary](16-glossary.md) · [diagrams](diagrams/README.md) |
| Status | [17 Phase 1 verification report](17-phase-1-verification-report.md) · [19 Phase 0 gap analysis](19-phase-0-gap-analysis.md) |
