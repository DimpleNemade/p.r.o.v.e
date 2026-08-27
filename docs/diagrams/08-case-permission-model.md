# Case permission model

```mermaid
flowchart TD
  U[User] --> R{Role}
  R -->|Administrator| All[All cases]
  R -->|Supervisor / Investigator| P[Case participant permission]
  R -->|Reviewer| Review[Review operations]
  R -->|Auditor| Read[Read-only case view]
```
