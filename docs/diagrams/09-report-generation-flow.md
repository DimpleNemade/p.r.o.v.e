# Report-generation flow

```mermaid
flowchart LR
  F[Findings] --> S[Supporting evidence]
  P[Provenance] --> D[Draft assembler]
  S --> D
  F --> D
  D --> R[Report draft]
  R --> X[Controlled export placeholder]
```
