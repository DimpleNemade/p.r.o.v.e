# Evidence lifecycle

```mermaid
stateDiagram-v2
  [*] --> Registered
  Registered --> Verifying
  Verifying --> Verified
  Verifying --> Mismatch
  Verified --> Processing
  Processing --> Normalized
  Processing --> Failed
```
