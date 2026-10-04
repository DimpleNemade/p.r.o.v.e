# Phase 3 progress and decisions

Final local verification: 2026-09-09  
Baseline revision: `537309e`

No applicable `AGENTS.md` was present. All baseline and current verification used
disposable database, evidence and output roots. The normal development database and
existing investigator evidence were neither migrated nor seeded.

## Final status

| Gate | Status | Local evidence |
| --- | --- | --- |
| 3A — isolation, integrity, evidence boundary, permissions and configuration | IMPLEMENTED AND VERIFIED locally | archived regressions, 45-test Django pass, clean profile/deployment checks |
| 3B — idempotent jobs, worker boundary, time semantics and independent review | IMPLEMENTED, VERIFICATION BLOCKED | eager/SQLite tests and two strict browser passes succeed; mandatory PostgreSQL/Redis/Celery/Linux-boundary run unavailable |
| 3C — verifiable audit and controlled export | IMPLEMENTED AND VERIFIED locally | ledger mutation tests, deterministic archive tests and two independently verified browser downloads |
| Overall Phase 3 | IMPLEMENTED, VERIFICATION BLOCKED | team-integration workflow exists but has not executed on suitable infrastructure |

Phase 3 is not complete because the team-integration gate remains blocked. No Phase 4
readiness claim is made.

## Baseline evidence

The archived revision passed 7 Django tests, 2 worker tests, 3 frontend tests and its
production build. Six security regressions then failed against that unchanged archive as
expected: generic self-approval, finding case reassignment, editor ownership grant,
auditor case creation, cross-case note/bookmark references and evidence reads outside
the configured root. The archived browser journey passed in isolated storage, so the
earlier browser failure was not reproduced and no cause was assigned to it.

## Decisions retained

- Evidence locators are relative to `<EVIDENCE_ROOT>/<case UUID>/`. Alternate absolute,
  traversal, stream, device, reserved and link/reparse forms fail closed. Legacy paths
  remain recorded but unreadable until an operator relocates them.
- SHA-256 is the only Phase 3 evidence digest. A blank external reference produces
  `baseline_pending`; explicit local acceptance records actor, reason, time and limits.
  No observation implicitly overwrites an accepted baseline.
- Account capability intersects case membership. No administrator bypass weakens case
  isolation or independent review.
- Django 5.2.17 LTS and DRF 3.16.1 replace their unsupported Phase 2 versions. Vitest
  5.0.0 removes the affected test-server dependency line.
- The local audit chain detects changes but cannot defeat a database administrator.
  Tail deletion requires a separately retained checkpoint. Export checksums establish
  consistency, not author authentication.

## Executed verification

| Check | Result |
| --- | --- |
| Full Django discovery from `apps/api` | PASS — 45 tests executed successfully; the unavailable integration class was skipped (2 collected methods) |
| Pytest API collection | PASS — 8 passed, 2 integration tests skipped |
| Standalone worker | PASS — 2 passed |
| Ruff lint and format | PASS — 108 Python files formatted |
| Migrations and normal system check | PASS — no model changes and zero issues |
| OpenAPI generation and validation | PASS — canonical `/api/v1` schema generated without warnings |
| Hardened team settings deployment check | PASS — zero issues with explicit synthetic configuration |
| Clean Python install and `pip check` | PASS — no broken requirements |
| Clean `npm ci` and audit | PASS — 345 packages audited, zero vulnerabilities |
| Vitest, TypeScript, Prettier and production Vite build | PASS — 3 tests and 88 transformed modules |
| Current browser workflow, clean root 1 | PASS — verify POST 200, processing POST 201, independent review, report and download |
| Current browser workflow, clean root 2 | PASS — same strict assertions in a distinct case/database/storage root |
| Offline verification of browser package 1 | PASS — `prove.handoff/1`, digest `9b45d98a39a04dbf953b03991db370285a08d296927215cfe7bf3bf5efb74715`, checkpoint 29 |
| Offline verification of browser package 2 | PASS — `prove.handoff/1`, digest `07da6c61b3640c148b4b9983c93b67b21b34dfcb3da5eb7fb7053e8a5779d96c`, checkpoint 29 |
| Prior-schema additive migration smoke | PASS — 1 case, 3 evidence rows and 3 reference hashes preserved; one legacy checkpoint added; ledger verified |
| Mermaid validation | PASS — source checked 64 Markdown files; parsed/rendered 8 Phase 3 diagrams to SVG and PNG |
| Mermaid visual inspection | PASS — all 8 PNGs readable and unclipped; the two wide ledger/export flows intentionally preserve horizontal sequence |
| PostgreSQL concurrent ledger/job claims | VERIFICATION BLOCKED — no local PostgreSQL service or Docker CLI |
| Redis publication and real Celery delivery/redelivery | VERIFICATION BLOCKED — no local Redis/Celery stack or Docker CLI |
| Linux bubblewrap no-network/read-only/limit enforcement | VERIFICATION BLOCKED — bubblewrap is unavailable on this Windows host |
| GitHub Actions workflow | IMPLEMENTED, NOT EXECUTED in this workspace |

During final acceptance, the browser gate exposed an evidence-list ordering error and a
verify/process write race. The ordering now uses `registered_at`; a regression assertion
covers the endpoint; evidence actions serialize in the UI; and the browser test requires
the actual verify and job responses to be 200 and 201. Both clean final runs passed after
those fixes.

Generated diagram artifacts are under `docs/generated/mermaid/`. Downloaded acceptance
packages are retained only in ignored `.phase3/` working evidence and are not release
artifacts.
