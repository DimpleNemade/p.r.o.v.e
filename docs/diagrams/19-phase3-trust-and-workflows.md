# Phase 3 trust boundaries and workflows

These eight diagrams are the maintained Phase 3 system views. Generated SVGs live in
`docs/generated/phase3`; the verifier parses and renders every changed source.

## Architecture and trust boundaries

```mermaid
flowchart TB
  UI[Investigator and reviewer UI] -->|session plus CSRF| API[Django API policy boundary]
  API --> DB[(PostgreSQL system of record)]
  API --> REDIS[Redis broker]
  REDIS --> WORKER[Celery orchestration worker]
  ROOT[(Case evidence root)] -->|read only locator| WORKER
  WORKER -->|immutable bounded snapshot| CHILD[Restricted metadata child]
  CHILD -->|schema checked output| WORKER
  WORKER --> OUT[(Private output and scratch)]
  CHILD -. no network namespace .- X[No external network]
```

## User and engine workflow

```mermaid
sequenceDiagram
  participant I as Investigator
  participant A as API
  participant W as Worker
  participant R as Reviewer
  I->>A: Register case-relative source
  I->>A: Observe digest
  alt operator reference exists
    A-->>I: Reference matched or mismatch
  else no external reference
    A-->>I: Baseline pending
    I->>A: Accept baseline with reason
  end
  I->>A: Submit idempotent job
  A->>W: Publish after commit
  W->>A: Atomic artifact and provenance commit
  I->>A: Submit supported finding revision
  R->>A: Independent review decision
  I->>A: Capture and download handoff
```

## Evidence states

```mermaid
stateDiagram-v2
  [*] --> Unverified
  Unverified --> BaselinePending: first local observation
  BaselinePending --> BaselineAccepted: explicit actor reason
  Unverified --> Verified: operator reference matches
  Verified --> Mismatch: later observation differs
  BaselineAccepted --> Mismatch: later observation differs
  Mismatch --> Verified: recorded reference matches again
  Mismatch --> BaselineAccepted: accepted baseline matches again
  Unverified --> Unreadable: denied or unreadable source
  Unreadable --> BaselinePending: readable without reference
  Unreadable --> Verified: readable and reference matches
```

## Job and retry states

```mermaid
stateDiagram-v2
  [*] --> Queued
  Queued --> Running: atomic claim token
  Queued --> Queued: broker retry
  Running --> Succeeded: atomic output commit
  Running --> Failed: bounded failure commit
  Running --> Queued: stale claim recovery
  Succeeded --> Succeeded: same job redelivery
  Failed --> [*]
  Succeeded --> Queued: intentional re-examination with reason
```

## Finding revision review

```mermaid
stateDiagram-v2
  [*] --> Draft
  Draft --> Submitted: bind text support provenance digest
  Submitted --> InReview: independent reviewer starts
  InReview --> Approved: support and integrity still valid
  InReview --> ChangesRequested: reviewer decision
  Submitted --> Withdrawn: author reason
  InReview --> Withdrawn: author reason
  Approved --> Draft: superseding revision reason
  ChangesRequested --> Draft: superseding revision reason
```

## Data relationships

```mermaid
erDiagram
  CASE ||--o{ EVIDENCE_ITEM : contains
  EVIDENCE_ITEM ||--o{ EVIDENCE_HASH : observes
  EVIDENCE_ITEM ||--o{ PROCESSING_JOB : targets
  PROCESSING_JOB ||--o{ PROCESSING_RUN : attempts
  PROCESSING_RUN ||--o{ ARTIFACT : creates
  EVIDENCE_ITEM ||--o{ PROVENANCE_LINK : originates
  ARTIFACT ||--o{ PROVENANCE_LINK : binds
  FINDING ||--o{ FINDING_REVISION : snapshots
  FINDING_REVISION ||--o{ REVIEW_DECISION : receives
  REPORT ||--o{ EXPORT_PACKAGE : captured_in
  CASE ||--o{ AUDIT_EVENT : sequences
```

## Event verification

```mermaid
flowchart LR
  L[Legacy rows] --> CP[Migration checkpoint digest]
  CP --> E1[Event sequence N]
  E1 -->|previous hash| E2[Event sequence N plus 1]
  C[Custody projection plus complete row digest] --> RD[Records digest]
  P[Provenance projection plus complete row digest] --> RD
  RD --> E2
  E2 --> V{Read only verifier}
  EXT[Separately retained checkpoint] --> V
  V --> OK[Valid with trust limitations]
  V --> BAD[Modification missing event or tail mismatch]
```

## Export generation and verification

```mermaid
flowchart LR
  PERM{Current export permission} -->|allowed| SNAP[Repeatable read case snapshot]
  SNAP --> CUT[Audit cutoff and checkpoint]
  CUT --> ALLOW[Explicit field allowlist]
  ALLOW --> CANON[Canonical JSON digest]
  CANON --> ZIP[Deterministic bounded ZIP]
  ZIP --> DL[Authorized download event after cutoff]
  ZIP --> OFF[Offline verifier]
  OFF --> SAFE{Entry path size and duplicate checks}
  SAFE --> HASH[Manifest and reference checks]
  HASH --> RESULT[Consistency result plus limitations]
```
