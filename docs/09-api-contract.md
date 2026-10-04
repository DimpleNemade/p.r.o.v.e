# API contract

Canonical routes use `/api/v1`; `/api` is a compatibility alias. JSON session writes need
CSRF. Collection responses are `{count, limit, offset, results}` with `limit` 1–100,
stable ordering and server-side filtering.

| Method | Route | Behavior |
| --- | --- | --- |
| GET | `/auth/csrf/` | issue the session write token |
| POST | `/auth/login/` | rate-limited session authentication |
| POST | `/auth/logout/` | end the authenticated session |
| GET | `/auth/me/` | current account identity and role |
| GET/POST | `/cases/` | accessible cases / authorized case creation |
| GET/POST | `/cases/{case}/participants/` | list / owner-controlled membership creation |
| GET/POST | `/cases/{case}/evidence/` | list / case-relative evidence registration |
| GET | `/evidence/{evidence}/` | redacted locator, observations and custody |
| GET/POST | `/evidence/{evidence}/verify/` | status / new integrity observation |
| POST | `/evidence/{evidence}/accept-baseline/` | explicit reasoned local acceptance |
| GET/POST | `/cases/{case}/jobs/` | list / idempotent submit or reasoned rerun |
| GET | `/jobs/{job}/` | state, attempts and reproducibility |
| GET | `/cases/{case}/artifacts/?q=` | database-filtered artifact page |
| GET | `/artifacts/{artifact}/provenance/` | stored evidence/run/link/timeline/finding relationships |
| GET/POST | `/cases/{case}/findings/` | list / draft creation |
| GET/PATCH | `/findings/{finding}/` | detail / versioned draft-content edit only |
| GET/POST | `/findings/{finding}/support/` | list / draft-only traceable support |
| POST | `/findings/{finding}/transition/` | submit/start_review/approve/request_changes/withdraw/supersede |
| GET/POST | `/cases/{case}/reports/` | list / draft snapshot; no approval side effect |
| GET | `/cases/{case}/audit/` | case event page |
| POST | `/cases/{case}/exports/` | capture and create package; returns status/download URL |
| GET | `/exports/{package}/` | current authorized status |
| GET | `/exports/{package}/download/` | current authorized private download |

Job creation accepts `evidence`, optional `{parameters:{}}`, and for re-examination
`prior_job`, non-empty `reason`, and unique `request_key`. Finding transitions require
`action`, current integer `version`, and comments for review decisions/revision reasons.

Common responses: `200` success, `201` durable creation, `204` logout, `400` validation
or unreadable source, `403` current capability/membership denied, `404` unknown resource,
`409` stale version or integrity prerequisite. OpenAPI is at `/api/schema/` and Swagger
UI at `/api/docs/`.

## Examples

All IDs below are illustrative. A browser session must send its `sessionid` cookie and
the current CSRF token on writes.

```http
GET /api/v1/cases/CASE-ID/evidence/?limit=50&offset=0

200 OK
{"count":3,"limit":50,"offset":0,"results":[{"id":"EVIDENCE-ID","source_locator":"synthetic-evidence.txt","verification_status":"verified"}]}
```

```http
POST /api/v1/cases/CASE-ID/jobs/
Content-Type: application/json
X-CSRFToken: TOKEN

{"evidence":"EVIDENCE-ID"}

201 Created
{"id":"JOB-ID","status":"succeeded","fingerprint":"SHA256-HEX","publication_status":"published"}
```

A deliberate re-examination is distinct from redelivery:

```json
{
  "evidence": "EVIDENCE-ID",
  "prior_job": "PRIOR-JOB-ID",
  "reason": "Parser version validation",
  "request_key": "operator-ticket-1842",
  "parameters": {}
}
```

Independent review uses the current optimistic version:

```http
POST /api/v1/findings/FINDING-ID/transition/

{"action":"approve","version":3,"comments":"Supporting revision and provenance independently checked."}
```

Export creation returns a status resource and a private download route. The downloaded
ZIP can be verified without Django or network access:

```powershell
python scripts\verify_package.py prove-PACKAGE-ID.zip
```
