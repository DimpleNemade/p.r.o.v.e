# Processing jobs

The worker interface is `submit_job`, `get_job_status`, `process_evidence`, `record_processing_run`, `record_artifact`, `record_provenance`, and `record_failure`. Celery dispatches jobs through Redis in asynchronous deployments. Eager mode is supported for local tests. V0.1 uses a basic metadata processor only.

```mermaid
sequenceDiagram
  participant UI as Investigator UI
  participant API as API
  participant R as Redis
  participant W as Worker
  UI->>API: Submit evidence job
  API->>R: Enqueue job
  R->>W: Deliver job
  W->>W: Hash and inspect metadata
  W->>API: Record run, artifact, provenance
  API-->>UI: Status and results
