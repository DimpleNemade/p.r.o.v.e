# Processing, retries and recovery

A fingerprint binds case, evidence identity, accepted input digest, processor/version,
normalized parameters and output schema. The default request key reuses one job for that
fingerprint. A deliberate re-examination creates a new job only with a unique key, prior
job and reason; earlier runs remain intact.

The API commits the queued job and audit event before publishing. Publication failures
set a visible recovery state. `dispatch_jobs` republishes up to 100 queued jobs; its
explicit `--recover-stale` mode records interrupted attempts before requeueing expired
claims.

Workers claim with one conditional database update. Processing happens outside long
locks. Artifact, timeline, provenance, successful run/job and completion audit then commit
atomically. A database constraint permits one successful attempted run per job. Duplicate
delivery returns existing state and cannot repeat output or completion. Failures preserve
attempt/error state and cannot appear as successful support.

Reproducibility records input/output digests, fingerprint, processor/schema, normalized
parameters and relevant Python/Django versions without secrets. The metadata adapter
emits size and SHA-256 only. Unknown source time stays null.

Team execution requires Linux `bubblewrap`: new network namespace, cleared environment,
no capabilities, read-only mounted input, private temporary filesystem and CPU, address
space, output, descriptor and wall-time limits. The Compose worker also drops capabilities,
uses a read-only root and internal-only network. Local eager execution is synthetic mode
and does not prove the team boundary.
