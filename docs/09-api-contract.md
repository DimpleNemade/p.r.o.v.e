# API contract

The OpenAPI schema is served at `/api/schema/` and Swagger UI at `/api/docs/`
(drf-spectacular). This page is the human summary.

`/api/v1/` is the canonical application route prefix. The same data endpoints are also
mounted under `/api/` for compatibility with the Phase 1 scaffold. Auth is available at
both `/api/v1/auth/` and `/api/auth/`.

## Conventions

- **Transport:** JSON over REST. Auth is a session cookie; mutating requests need the
  `X-CSRFToken` header.
- **Access:** every data route requires an authenticated session. Reads require
  case read access; writes require case write access (`owner`/`edit`/`review`, or the
  `administrator` role).
- **Immutability:** custody, audit, and provenance have no update or delete routes.
- **IDs:** all resource IDs are UUIDs.

## Auth

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/auth/csrf/` | issue a CSRF token (open) |
| POST | `/api/auth/login/` | authenticate, create session (open, CSRF-checked) |
| POST | `/api/auth/logout/` | end session → `204` |
| GET | `/api/auth/me/` | current identity and role |

## Cases

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/cases/` | cases the caller owns or participates in |
| POST | `/api/v1/cases/` | create a case (caller becomes `owner` participant) → `201` |
| GET | `/api/v1/cases/{id}/` | case detail (`403` if no access) |

## Evidence

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/cases/{id}/evidence/` | list evidence in a case |
| POST | `/api/v1/cases/{id}/evidence/` | register evidence → `201` + custody + audit |
| GET | `/api/v1/evidence/{id}/` | evidence detail, hashes, custody, warnings, limitations |
| GET / POST | `/api/v1/evidence/{id}/verify/` | view or perform SHA-256 verification |

## Processing & investigation

| Method | Path | Purpose |
| --- | --- | --- |
| GET / POST | `/api/v1/cases/{id}/jobs/` | list / submit a processing job; requires verified evidence |
| GET | `/api/v1/jobs/{id}/` | processing job detail with runs |
| GET | `/api/v1/cases/{id}/artifacts/?q=` | list artifacts; `q` is a substring filter |
| GET | `/api/v1/artifacts/{id}/` | artifact detail |
| GET | `/api/v1/artifacts/{id}/provenance/` | artifact → run → evidence → timeline/finding chain |
| GET | `/api/v1/cases/{id}/timeline/` | chronological events with type/date filters |
| GET | `/api/v1/cases/{id}/provenance/` | list provenance links |
| GET / POST | `/api/v1/cases/{id}/findings/` | list / create a finding → `201` |
| GET / PATCH | `/api/v1/findings/{id}/` | finding detail/update |
| GET / POST | `/api/v1/findings/{id}/support/` | list / attach one artifact or timeline event |

## Reporting

| Method | Path | Purpose |
| --- | --- | --- |
| GET / POST | `/api/v1/cases/{id}/reports/` | list / generate a report draft from findings + provenance → `201` |
| GET | `/api/v1/reports/{id}/` | report detail / preview snapshot |
| GET | `/api/v1/cases/{id}/audit/` | case audit events |
| GET | `/api/v1/audit/` | caller's global login/logout events |
| POST | `/api/v1/cases/{id}/exports/` | request a controlled export → `202` placeholder receipt, no file |

## Status codes

`200` ok · `201` created · `202` accepted (export placeholder) · `204` no content
(logout) · `400` validation or unreadable evidence · `403` case access denied · `404` unknown
resource · `409` integrity prerequisite not met.

All implemented detail routes use explicit `404` handling. Raw evidence content is not
returned by any endpoint.
