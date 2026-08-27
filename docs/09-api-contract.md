# API contract

The OpenAPI schema is served at `/api/schema/` and Swagger UI at `/api/docs/`.

Core routes: `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/me/`, `/api/cases/`, `/api/cases/{id}/evidence/`, `/api/evidence/{id}/verify/`, `/api/cases/{id}/jobs/`, `/api/cases/{id}/artifacts/?q=`, `/api/cases/{id}/provenance/`, `/api/cases/{id}/findings/`, `/api/findings/{id}/support/`, `/api/cases/{id}/reports/`, `/api/cases/{id}/audit/`, and `/api/cases/{id}/exports/`.

All data routes require an authenticated session. Write operations require case write permission. Custody, audit, and provenance have no update/delete routes.
