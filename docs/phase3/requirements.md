# Phase 3 requirements traceability matrix

Status reflects evidence available on 2026-09-09. `VERIFICATION BLOCKED` means the code
and executable check exist but the required local infrastructure did not.

| ID | Requirement | Implementation | Behavioral verification | Status |
| --- | --- | --- | --- | --- |
| A01 | Dedicated DB/evidence/output/ports; no reuse | `config/test_settings.py`, `scripts/start_e2e_api.py`, Playwright config | isolated archived and current browser runs | IMPLEMENTED AND VERIFIED |
| A02 | Non-destructive explicit synthetic setup | `seed_demo` create-once fixture identity | clean and repeated seed preserves password/hash/job/finding/report/counts | IMPLEMENTED AND VERIFIED |
| A03 | Honest reference/pending/accepted/mismatch/unreadable states | `evidence/services.py`, model fields, UI/export labels | integrity state and validation tests | IMPLEMENTED AND VERIFIED |
| A04 | Explicit immutable baseline and all observations | acceptance endpoint, `EvidenceHash` observations | stale acceptance, overwrite, changed-input tests | IMPLEMENTED AND VERIFIED |
| A05 | Root/case/path/link/special-file boundary | `evidence/storage.py` | traversal, drive, UNC, device, reserved, reparse, outside-root tests | IMPLEMENTED AND VERIFIED |
| A06 | Same opened bounded source and modification checks | `read_source`, immutable bytes | mutation and size-limit tests | IMPLEMENTED AND VERIFIED |
| A07 | Account role ∩ membership policy | `cases/permissions.py`, server action map | escalation, auditor, reviewer tests | IMPLEMENTED AND VERIFIED |
| A08 | Immutable fields and cross-case FK/detail protection | scoped serializers/views | case reassignment, support, note, bookmark and provenance tests | IMPLEMENTED AND VERIFIED |
| A09 | Dev/test/team hardening and login abuse limit | settings profiles, login cache/logging | subprocess rejection tests and zero-warning deployment check | IMPLEMENTED AND VERIFIED locally |
| A10 | Supported dependencies | Django 5.2.17, DRF 3.16.1, Vitest 5.0.0 | checks/build/tests/audits | IMPLEMENTED AND VERIFIED |
| B01 | Redelivery versus reasoned re-examination/fingerprint | processing model/service | reuse, rerun, redelivery tests | IMPLEMENTED AND VERIFIED |
| B02 | Concurrent claim, atomic output/failure, attempts | conditional claim, DB constraint, transactions | SQLite redelivery/rollback; PostgreSQL job configured | IMPLEMENTED, VERIFICATION BLOCKED |
| B03 | Post-commit publication and recovery | `on_commit`, publication state, `dispatch_jobs` | injected broker failure/recovery; real broker configured | IMPLEMENTED, VERIFICATION BLOCKED |
| B04 | Restricted read-only/no-network/limited child | `processing/boundary.py`, team Compose | fail-closed/size local tests; Linux boundary CI job | IMPLEMENTED, VERIFICATION BLOCKED |
| B05 | Source/registration/process/review time separation | timeline fields and legacy label migration | null source-time/legacy upgrade tests | IMPLEMENTED AND VERIFIED |
| B06 | Stored/incomplete provenance rendering | API boundary and dynamic UI chain | missing traceability blocks submission | IMPLEMENTED AND VERIFIED |
| B07 | Independent immutable revision review | revision/decision models and transitions | self-review, submit/start/approve/supersede tests; two-account browser | IMPLEMENTED AND VERIFIED |
| B08 | Optimistic concurrency and integrity effect | finding version and approval revalidation | stale version/integrity failure tests | IMPLEMENTED AND VERIFIED |
| B09 | Reports bind exact approved revisions | report snapshot generation | browser and review suite | IMPLEMENTED AND VERIFIED |
| B10 | Stable refresh/selection/errors/pagination | stale-load guard, ID rebinding, action UI, paged API/client | pagination test, browser journey, TypeScript checks | IMPLEMENTED AND VERIFIED |
| C01 | Canonical sequenced chain with actor/service/record binding | audit canonical/records/services | mutation, missing/reordered, record tamper tests | IMPLEMENTED AND VERIFIED locally |
| C02 | Legacy checkpoint and read-only verifier | additive migration, `verify_ledger` | prior-schema upgrade and non-repair tests | IMPLEMENTED AND VERIFIED |
| C03 | Authorized create/status/download with revocation | reporting service/views | real download and post-capture revocation tests | IMPLEMENTED AND VERIFIED |
| C04 | Consistent allowlisted cutoff snapshot/deterministic digest | reporting snapshot/package | byte stability, cutoff, redaction, case/reference tests | IMPLEMENTED AND VERIFIED |
| C05 | Offline safe malformed-archive verification | `reporting/package.py`, `scripts/verify_package.py` | altered/missing/substituted/traversal/duplicate tests and downloaded package | IMPLEMENTED AND VERIFIED |
| D01 | Maintained docs, risks, ADRs, migration/backup | README, docs 03–13, phase3 records, ADR 011–015 | source review and link/search checks | IMPLEMENTED AND VERIFIED |
| D02 | Mermaid source/parse/render/visual check | diagram 19, Python validator, Mermaid CLI | final outcomes in progress record | IMPLEMENTED AND VERIFIED |
| V01 | Full discovery/lint/format/build/dependencies | scripts and CI | 45 Django, 2 worker, 3 frontend; clean installs/audits/build pass | IMPLEMENTED AND VERIFIED locally |
| V02 | Two clean browser runs plus retained seed/redelivery | isolated launcher, backend regressions | two fresh strict passes and two offline-verified packages | IMPLEMENTED AND VERIFIED |
| V03 | PostgreSQL/Celery/Redis/clean upgrade/install | integration settings/test, workflow, team Compose | upgrade smoke passed; team stack unavailable | IMPLEMENTED, VERIFICATION BLOCKED |
