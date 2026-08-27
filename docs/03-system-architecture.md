# System architecture

The browser and Tauri shell use the same React application. Django/DRF owns the system of record, session authentication, case authorization, and provenance. PostgreSQL is the intended team database; SQLite is a local fallback. Celery and Redis provide asynchronous processing, with eager synchronous mode for development.

```mermaid
flowchart LR
  UI[React investigator UI] --> API[Django REST API]
  DESK[Tauri 2 shell] --> UI
  API --> DB[(PostgreSQL / SQLite)]
  API --> Q[Redis queue]
  Q --> W[Python forensic worker]
  W --> DB
  API --> AUD[Append-only audit and provenance]
```

See [deployment topology](diagrams/10-deployment-topology.md) and [ADRs](decisions/README.md).
