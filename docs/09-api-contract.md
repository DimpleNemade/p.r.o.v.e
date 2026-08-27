# API contract

The OpenAPI schema is served at `/api/schema/` and Swagger UI at `/api/docs/`
(drf-spectacular). This page is the human summary.

## Conventions

- **Transport:** JSON over REST. Auth is a session cookie; mutating requests need the
  `X-CSRFToken` header.
- **Access:** every `/api/` data route requires an authenticated session. Reads require
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
| GET | `/api/cases/` | cases the caller owns or participates in |
| POST | `/api/cases/` | create a case (caller becomes `owner` participant) → `201` |
| GET | `/api/cases/{id}/` | case detail (`403` if no access) |

## Evidence

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/cases/{id}/evidence/` | list evidence in a case |
| POST | `/api/cases/{id}/evidence/` | register evidence → `201` + custody + audit |
| POST | `/api/evidence/{id}/verify/` | compute + compare SHA-256; `400` if unreadable |

## Processing & investigation

| Method | Path | Purpose |
| --- | --- | --- |
| GET / POST | `/api/cases/{id}/jobs/` | list / submit a processing job → `201` |
| GET | `/api/cases/{id}/artifacts/?q=` | list artifacts; `q` is a substring filter |
| GET | `/api/cases/{id}/provenance/` | list provenance links |
| GET / POST | `/api/cases/{id}/findings/` | list / create a finding → `201` |
| POST | `/api/findings/{id}/support/` | attach an artifact or timeline event → `201` |

## Reporting

| Method | Path | Purpose |
| --- | --- | --- |
| GET / POST | `/api/cases/{id}/reports/` | list / generate a report draft from findings + provenance → `201` |
| GET | `/api/cases/{id}/audit/` | list audit events (newest first) |
| POST | `/api/cases/{id}/exports/` | request a controlled export → `202` placeholder receipt, no file |

## Status codes

`200` ok · `201` created · `202` accepted (export placeholder) · `204` no content
(logout) · `400` invalid credentials or unreadable evidence · `403` case access denied.

**Known gap:** detail routes call `Model.objects.get(...)` without catching
`DoesNotExist`, so an unknown ID currently returns `500` instead of `404`. Tracked in
[19 Phase 0 gap analysis](19-phase-0-gap-analysis.md).
