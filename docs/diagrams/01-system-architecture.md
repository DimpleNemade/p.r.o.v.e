# System architecture

```mermaid
flowchart LR
  UI[React UI] --> API[Django API]
  API --> DB[(PostgreSQL)]
  API --> Q[Redis]
  Q --> W[Python worker]
```
