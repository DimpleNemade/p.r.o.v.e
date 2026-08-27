# Evidence lifecycle

Registration records the logical source and acquisition metadata. Verification calculates SHA-256 without changing the source. Processing is stopped on unreadable paths or hash mismatch. Successful runs produce basic metadata artifacts and provenance links. No V0.1 endpoint modifies or deletes original evidence.

```mermaid
flowchart TD
  A[Register acquired evidence] --> B[Read-only path check]
  B --> C[Calculate SHA-256]
  C --> D{Matches expected hash?}
  D -- No --> F[Record mismatch and stop]
  D -- Yes --> E[Queue processing job]
  E --> G[Create normalized artifact]
  G --> H[Record provenance and timeline]
