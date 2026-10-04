# System architecture

P.R.O.V.E. is a Django/DRF modular monolith with a React/TypeScript client and optional
Tauri shell. PostgreSQL is the team system of record; SQLite is local only. Celery/Redis
orchestrates team jobs. Evidence processing occurs in a separate bounded child, because
Celery itself is not a hostile-input sandbox.

The API owns authorization and every durable business transition. Evidence storage and
private output are disjoint. A case-relative locator is resolved only below that case's
evidence directory. One bounded immutable byte snapshot feeds both integrity comparison
and processing. Derived artifacts, provenance, finding revisions, audit chains and export
snapshots live in the database or private output root.

Development is explicitly synthetic and uses eager processing. Team configuration fails
closed when secrets, PostgreSQL, Redis, HTTPS origins, hosts or storage are invalid. See
[architecture and controls](phase3/architecture-and-controls.md),
[team operations](phase3/operations.md), and the
[current diagrams](diagrams/19-phase3-trust-and-workflows.md).

The API and worker do not return raw evidence bytes. A `read_only` database value records
intent; operating-system mounts and permissions enforce host-level write protection.
Path/stat checks reduce replacement risk but cannot prove complete protection from every
concurrent filesystem modification.
