# User workflows

```mermaid
flowchart TD
  A[Create case] --> B[Register evidence]
  B --> C[Verify hash]
  C --> D[Process]
  D --> E[Search artifacts]
  E --> F[Inspect provenance]
  F --> G[Create finding]
  G --> H[Attach supporting evidence]
  H --> I[Generate report draft]
  I --> J[Review audit history]
  J --> K[Request controlled export]
```

The interface exposes loading, empty, processing, failure, denied, unsupported, mismatch, verified, no-findings, missing-provenance, and unsaved-change states as the product matures.
