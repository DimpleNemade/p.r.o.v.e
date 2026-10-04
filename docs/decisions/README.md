# Architecture decision records

Each ADR records one decision in a fixed shape: **Context → Decision → Consequences**,
with a status and date. They are immutable once accepted; a reversal is a new ADR that
supersedes the old one.

| ADR | Decision | Status |
| --- | --- | --- |
| [001](001-django-foundation.md) | Django as platform foundation | accepted |
| [002](002-drf-api.md) | Django REST Framework as API layer | accepted |
| [003](003-react-typescript.md) | React + TypeScript investigator interface | accepted |
| [004](004-tauri-shell.md) | Tauri desktop shell | accepted |
| [005](005-postgresql.md) | PostgreSQL as shared team database | accepted |
| [006](006-worker-separation.md) | Separate Python forensic worker | accepted |
| [007](007-celery-redis.md) | Celery + Redis for processing jobs | accepted |
| [008](008-v01-exclusions.md) | Exclude high-risk capabilities from V0.1 | accepted |
| [009](009-provenance-first.md) | Provenance as a first-class data model | accepted |
| [010](010-core-investigator-workflow.md) | Explicit, versioned investigator workflow | accepted |
| [011](011-case-evidence-storage.md) | Case-relative evidence storage boundary | accepted |
| [012](012-accepted-processing-baseline.md) | Explicit accepted processing baseline | accepted |
| [013](013-idempotent-processing.md) | Database-backed processing identity | accepted |
| [014](014-revision-review.md) | Immutable revisions and independent review | accepted |
| [015](015-audit-and-export.md) | Canonical audit and deterministic handoff | accepted |
