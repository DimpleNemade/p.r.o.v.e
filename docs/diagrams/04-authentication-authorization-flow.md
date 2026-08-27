# Authentication and authorization flow

```mermaid
sequenceDiagram
  User->>API: Login
  API-->>User: Secure session
  User->>API: Case request
  API->>API: Role and membership check
  API-->>User: Allow or deny
```
