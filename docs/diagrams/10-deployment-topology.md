# Deployment topology

```mermaid
flowchart TB
  B[Browser or Tauri shell] --> API[API process]
  API --> PG[(PostgreSQL)]
  API --> REDIS[(Redis)]
  REDIS --> WORKER[Worker process]
  WORKER --> STORE[Restricted evidence storage]
```
