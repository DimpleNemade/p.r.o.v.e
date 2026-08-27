# Authentication and authorization

V0.1 uses a custom Django user model, secure password hashing, session authentication, CSRF protection, HttpOnly/SameSite cookies, explicit CORS, and Django groups/permissions as the extension point. Case access is granted through `CaseParticipant` permission levels. Administrators bypass case membership; ordinary users do not.

```mermaid
sequenceDiagram
  participant U as User
  participant W as Web UI
  participant A as Django API
  U->>W: Enter credentials
  W->>A: POST /api/auth/login/
  A->>A: Authenticate and create secure session
  A-->>W: Identity and session cookie
  W->>A: Case request + CSRF token
  A->>A: Check role and case participant
  A-->>W: Data or permission denied
