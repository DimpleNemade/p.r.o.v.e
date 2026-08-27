# Validation and testing

Backend coverage targets system checks, models, authentication, case isolation, hashing, provenance, audit, APIs, worker success/failure, and permissions. Run `powershell.exe -ExecutionPolicy Bypass -File .\scripts\run_backend_tests.ps1` from the repository root; it runs the Django suite and the forensic-worker suite and prints collection/count output. The direct Django command is `.\.venv\Scripts\python.exe apps\api\manage.py test`.

Frontend checks are run from `apps/web` with `npm.cmd run lint`, `npm.cmd run test`, `npm.cmd run build`, `npm.cmd run format:check`, and `npm.cmd run e2e`. The E2E suite currently verifies the login screen without requiring a live API; full authenticated workflow coverage requires the API and seeded database to be running.

The synthetic worker tests verify SHA-256 success, mismatch failure, and absence of raw content in result data. This is software verification, not validation of forensic parser correctness.
