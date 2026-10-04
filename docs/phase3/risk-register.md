# Phase 3 prioritized risk register

| Priority | Risk | Current control | Residual/action |
| --- | --- | --- | --- |
| P0 | PostgreSQL/Celery behavior differs from SQLite/eager | executable CI integration suite, DB constraints, atomic claim | mandatory gate remains blocked until CI or team stack passes |
| P0 | Worker boundary cannot create its namespaces | fail-closed team mode; no unrestricted fallback | run team Compose/CI on supported Linux and record kernel/user-namespace policy |
| P0 | Privileged administrator rewrites database and chain | canonical chain plus external checkpoint support | retain checkpoints outside DB; operational access controls and backups required |
| P1 | Evidence changes during read | same open handle, bounded immutable snapshot, before/after identity checks | platform/filesystem behavior cannot provide absolute protection; immutable storage or snapshot technology recommended |
| P1 | Legacy absolute locator is unusable | preserved and redacted; read denied | documented operator relocation/custody procedure required per case |
| P1 | Package author cannot be authenticated | deterministic content and checksums | design signing keys, rotation, revocation and recipient trust before adding signatures |
| P1 | Package size/record limits omit large cases | explicit 32 MiB/10,000-record refusal | add streamed bounded packaging and documented selection policy later |
| P2 | Login limiter is shared through Redis only in team profile | five-minute, ten-attempt limit with safe logging | choose deployment-specific edge rate limits and retention policy |
| P2 | Metadata adapter correctness is narrow | known byte digest, size and schema checks | Phase 4 known-answer corpus must measure record-level correctness |
| P2 | Tauri shell not exercised | optional and outside core acceptance | validate separately before desktop distribution |

No row claims certification, compliance approval, legal admissibility or forensic parser
validation.
