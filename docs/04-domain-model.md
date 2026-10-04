# Domain model

| Area | Durable records and invariants |
| --- | --- |
| Identity/case | `User`, `Case`, `CaseParticipant`; account capability intersects membership; case owner and owner membership are consistent |
| Evidence | `EvidenceItem`, append-only `EvidenceHash`, `CustodyEvent`; operator reference and immutable accepted baseline are separate |
| Processing | `ProcessingJob`, `ProcessingRun`; constrained idempotency key, fingerprint, prior-run relationship, claim/attempt identity and reproducibility fields |
| Investigation | `Artifact`, `TimelineEvent`, `ProvenanceLink`, `Finding`, `FindingSupport`, immutable `FindingRevision`, append-only `ReviewDecision` |
| Reporting | draft `Report` snapshots and private `ExportPackage` delivery metadata/snapshot |
| Audit | `AuditEvent` with case sequence, schema, actor/service, previous/event hash and custody/provenance bindings |

All primary IDs are UUIDs. Foreign-key policies retain actors, inputs, runs, revisions and
reports needed for traceability. Ordinary APIs expose no update/delete for custody,
provenance, revisions, review decisions or audit events. Collection APIs use a stable
secondary UUID order and bounded `limit`/`offset` pages.

`TimelineEvent.observed_at` is nullable because unknown source time must stay unknown.
Original value/format, zone, meaning, precision and uncertainty are stored separately.
Legacy generated timestamps are retained and explicitly labelled.

The full relationship view is in the
[Phase 3 diagram set](diagrams/19-phase3-trust-and-workflows.md#data-relationships).
