# Authentication and authorization

Sessions use CSRF protection, HttpOnly/SameSite cookies and secure cookies outside
development. Team mode requires explicit HTTPS origins and hosts. Failed login attempts
use a five-minute, ten-attempt cache bucket derived from the remote address; safe logs
record only its digest and never credentials.

Authorization is one server policy: account capability intersects an active case
membership. There is no administrator or superuser case-access bypass. The complete
[role/action matrix](phase3/architecture-and-controls.md) covers administrator,
supervisor, investigator, reviewer, auditor and student.

Participant management needs owner membership and owner consistency. Ordinary creation
cannot grant owner or a membership incompatible with the target account. Case/review
fields are unavailable through generic finding updates. Every supplied relationship is
validated against the enclosing case before save, and nested artifact/provenance reads
also validate their stored boundary.

Finding approval always requires a different authorized reviewer. An administrator who
authored a finding cannot approve it through the normal application. UI action controls
come from the same server decision and are convenience only; the API remains authoritative.
