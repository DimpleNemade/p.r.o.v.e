# Phase 3 implementation and verification report

Date: 2026-09-09  
Baseline: Git revision `537309e`  
Scope: evidence integrity, investigation controls, reproducible handoff

## Status

| Milestone | Status | Evidence |
| --- | --- | --- |
| 3A — isolation, evidence and access controls | IMPLEMENTED AND VERIFIED locally | isolated regression suite, path and baseline tests, repeated seed, profile checks |
| 3B — reliable processing and independent review | IMPLEMENTED, VERIFICATION BLOCKED | SQLite/eager behavior and two-account browser journey pass; PostgreSQL concurrency, real Redis/Celery and Linux restricted child await CI/infrastructure execution |
| 3C — audit verification and controlled export | IMPLEMENTED AND VERIFIED locally | mutation/missing/tail tests, real package download, deterministic snapshot test and standalone offline verification |
| Overall Phase 3 | IMPLEMENTED, VERIFICATION BLOCKED | mandatory team-integration gate has an executable CI job but was not run locally because Docker is unavailable |

This status does not establish forensic parser validity, legal admissibility, certification,
or production readiness.

## Baseline findings

The archived source passed seven Django tests, two standalone worker tests, three frontend
tests and a production build. Six new regression tests failed against that revision:
generic self-approval, finding case reassignment, editor ownership grant, auditor case
creation, cross-case note/bookmark references, and evidence reads outside the configured
root. The source also showed that blank reference hashes were treated as verified, job
redelivery could duplicate output, export emitted no file, seed rewrote state/passwords,
and Playwright reused normal servers and data.

The earlier browser failure was not reproduced: the archived journey passed in an
isolated copy. No causal claim about duplicate artifacts is made. Source inspection did
find that refresh replaced the workspace with a loading screen; the UI now retains its
mounted detail state, ignores stale loads, and rebinds finding selection by identifier.

## Implemented controls

- Evidence sources are case-relative logical locators below
  `<EVIDENCE_ROOT>/<case UUID>/`. Absolute, drive-relative, UNC, device, traversal,
  alternate-stream, reserved-name, symlink, junction/reparse and special-file sources
  fail closed. The opened regular file is bounded and copied to immutable bytes used for
  both SHA-256 and metadata processing. Identity/size/time checks detect replacement or
  modification around the read. They reduce, but do not completely eliminate, all
  concurrent modification risk.
- An operator reference, a local observation, explicit local baseline acceptance,
  comparison success, mismatch and unreadable state are distinct. Local acceptance
  records actor, time, reason and limitations. Every observation is retained and the
  processing baseline is never replaced implicitly.
- Account capability intersects case membership. Administrators have no cross-case or
  review-independence bypass. Foreign-key case consistency is checked before writes;
  nested provenance reads reject contaminated relationships. Generic finding PATCH
  cannot change case or review state. Participant creation cannot grant ownership.
- Profiles are explicit: development, disposable test and fail-closed team. Team mode
  requires PostgreSQL, Redis, secure origins/hosts, strong secret, real storage and
  asynchronous Celery. Login failures are bounded by an address-digest cache key and
  logs never contain passwords.
- Job request identity is a database constraint. One default fingerprint reuses one job;
  a deliberate rerun needs a prior job, reason and idempotency key. Atomic conditional
  claim prevents duplicate delivery, processing occurs outside the claim transaction,
  and outputs/provenance/completion/audit commit together. Failed broker publication is
  visible and `dispatch_jobs` retries queued work or explicitly recovers expired claims.
- Team processing invokes a `bubblewrap` child with a new network namespace, no
  capabilities, read-only input, private temporary space and CPU/memory/file/output/fd
  limits. There is no unsandboxed team fallback. Non-team processing accepts synthetic
  inputs only and is labelled synthetic development execution.
- Source-event time is independent of registration/processing/review time. Unknown stays
  null and carries meaning, precision and uncertainty fields. A migration labels legacy
  generated times without calling them source times.
- A submitted finding revision binds text, supports, input digests, run, processor,
  artifact content digest and provenance. An independent reviewer records start,
  approval or changes-requested decisions. Optimistic version checks prevent overwrite;
  approved revisions remain immutable when superseded. Report drafts bind exact approved
  revision snapshots and report generation never approves a finding.
- Audit events use `prove.audit/1` canonical JSON, a per-case atomic sequence, previous
  hash, actor/service separation, and custody/provenance record bindings. The read-only
  verifier detects modified, missing/reordered events and record changes. The migration
  adds a dated checkpoint without fabricating earlier trust.
- Export captures one case under a database transaction and records an explicit audit
  cutoff. The allowlist excludes evidence bytes, private paths, arbitrary metadata,
  credentials and other cases. Deterministic canonical snapshot content has a stable
  digest; delivery ID/time and post-cutoff download events remain separate. The offline,
  standard-library verifier never extracts files and rejects traversal, duplicate,
  encrypted/compressed, oversized, malformed, altered, missing and substituted entries.

## Investigator and reviewer walkthrough

1. An owner registers a file already staged under the case evidence directory using its
   relative locator and, when available, the operator reference SHA-256.
2. **Verify integrity** creates an observation. A match permits processing. With no
   reference, the state is **Baseline acceptance required** until the investigator enters
   a reason and accepts the limitations.
3. **Start processing** re-observes the accepted source, runs the bounded metadata child,
   then atomically stores run, artifact, unknown-time timeline record and provenance.
4. The investigator writes a finding, attaches a traceable artifact/timeline record, and
   submits a frozen revision.
5. A different account with reviewer capability opens the same case, starts review and
   records approval or requested changes with comments. The author cannot approve it.
6. The investigator creates a report draft containing exact approved revision snapshots,
   then captures and downloads a controlled package.
7. A recipient runs `python scripts/verify_package.py package.zip` offline and separately
   retains the checkpoint returned by the verifier.

## Migrations and compatibility

All migrations are additive. They add accepted baselines and observations, job identity
and attempts, timestamp semantics, finding revisions/decisions, audit chain fields,
legacy checkpoint and export snapshot/storage fields. The disposable upgrade smoke test
preserved one old case, three evidence records and all three existing hashes; it added one
legacy checkpoint and the resulting chain verified. Back up database, evidence and
private output together before migration. Absolute legacy locators remain recorded but
are returned as `legacy-source-relocation-required` and cannot be read until an operator
relocates them into approved case storage.

Django moved from unsupported 5.1.11 to 5.2.17 LTS; DRF moved from 3.15.2 to 3.16.1.
The version choice follows the [Django supported-version table](https://www.djangoproject.com/download/)
and the [DRF 3.16 compatibility announcement](https://www.django-rest-framework.org/community/3.16-announcement/),
checked on 2026-09-09.
Vitest moved from 3.2.7 to 5.0.0 to remove the known development-test server file-read
advisory. No existing migration was rewritten.

## Verification record

| Check | Result |
| --- | --- |
| Archived baseline | 7 Django, 2 worker, 3 frontend tests passed; production build passed |
| Archived risk reproduction | 6 of 6 security regressions failed as expected |
| Complete current Django discovery | passed: 45 tests executed; unavailable integration class skipped (2 collected methods) |
| Python Ruff lint and format | passed |
| Migration consistency and system check | passed |
| Prior-schema migration smoke | passed; cases/evidence/hashes preserved and checkpoint verified |
| pip dependency consistency | passed |
| TypeScript project build, Vitest, Prettier, Vite build | passed; 3 tests |
| npm audit at moderate threshold | passed with zero reported vulnerabilities |
| Archived browser reproduction | passed once in isolated storage; earlier failure not reproduced |
| Current two-account browser plus download | passed twice in fresh roots with strict verify 200 and processing 201 assertions; both packages verified offline |
| Mermaid source check, parse and SVG/PNG render | passed: 64 Markdown files source checked and 8 Phase 3 diagrams rendered and visually inspected |
| PostgreSQL concurrency, Redis/Celery and restricted Linux child | IMPLEMENTED, VERIFICATION BLOCKED locally; Docker command unavailable |
| CI | workflow written; CI has not run in this workspace |

## Trust limits

A local hash chain cannot defeat an administrator who can rewrite records and hashes.
Tail deletion is reliable only when a checkpoint is separately retained and trusted.
Checksums show agreement with the manifest; they do not authenticate its author. Signing
is deferred until key storage, rotation and trust distribution are designed. SQLite and
eager Celery results do not prove PostgreSQL concurrency or asynchronous reliability.

Requirements mapping: [Phase 3 matrix](phase3/requirements.md) ·
[risk register](phase3/risk-register.md) · [operations](phase3/operations.md) ·
[diagrams](diagrams/19-phase3-trust-and-workflows.md).
