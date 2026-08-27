# Security threat model

A working model for V0.1 — not a completed assurance artefact. The platform processes
**untrusted content** (evidence) and holds **highly sensitive case data**; both shape
the design.

## Trust boundaries

Browser · API · database · queue · worker · evidence storage.

## Threats and mitigations

| Threat | Mitigation in V0.1 |
| --- | --- |
| Unauthorized case access | `IsAuthenticated` on every route + `has_case_access` role/participant check |
| Arbitrary path exposure / traversal via `original_path` | intended `EVIDENCE_ROOT` boundary; read-only access; no raw content in responses |
| Silent hash mismatch | mismatch and unreadable states are blocking and written to custody + audit |
| Sensitive data in logs | worker and API never log raw evidence contents |
| Session replay / CSRF | `HttpOnly`/`SameSite` cookies, `Secure` in production, explicit CSRF check on login and mutations |
| Cross-origin abuse | explicit CORS + CSRF trusted-origin allowlists |
| Tampering with history | no update/delete routes for `AuditEvent`, `CustodyEvent`, `ProvenanceLink` |
| Worker failure masquerading as "no evidence" | job/run `failed` states with recorded `error` |
| Malicious evidence (parser exploitation, resource exhaustion) | processing isolated in a separate worker; **sandboxing, no-network, and resource limits are not yet implemented** |

## Residual risks (must be owned by the deployment)

- Deployment secret management and the production `SECRET_KEY`.
- OS-level permissions on evidence storage and `EVIDENCE_ROOT` enforcement.
- Backup/restore policy and tested recovery.
- Dependency supply chain — run `pip`/`npm` audits and pin before deployment.
- Worker isolation hardening (container, dropped capabilities, no egress).
- Full production hardening (`manage.py check --deploy`, HTTPS/HSTS).

Related: [07 Authentication & authorization](07-authentication-and-authorization.md) ·
[11 Data protection & privacy](11-data-protection-and-privacy.md) ·
[13 Deployment & operations](13-deployment-and-operations.md).
