# Processing-job sequence

```mermaid
sequenceDiagram
  API->>Redis: Enqueue
  Redis->>Worker: Deliver
  Worker->>Worker: Hash and inspect
  Worker->>API: Record results
```
