# Phase 1 verification report

## Executive result

Phase 1 partially completed. The browser/API/worker workflow is verified locally with SQLite and eager Celery. Tauri, PostgreSQL, Redis, Docker, and the production deployment profile remain unverified because the required workstation tooling is unavailable.

## Verification context

- Date: 2026-08-19 (this report is a point-in-time record; the repository was later placed under Git)
- Workspace: the project repository root
- Repository state at the time: not yet a Git checkout; no reset, checkout, deletion, or unrelated cleanup was performed.
- Initial assessment: the scaffold contains Django/DRF apps for identity, cases, evidence, processing, investigations, reporting, and audit; a React/Vite browser app; a Tauri shell; a synthetic worker; Docker Compose; 12 Mermaid documents; and an existing test/documentation set.
- Initial defect: root-level `python apps/api/manage.py test` collected zero tests because Django used the workspace root as its discovery root. The command now explicitly targets the `cases` app when no test label is supplied and discovers five tests.

## Environment summary

| Tool | Result |
| --- | --- |
| Windows | Windows 11 Home Single Language, 10.0.26200 build 26200 |
| Python | 3.12.4 |
| Virtual environment | `.venv` present |
| Django | 5.1.11 |
| Django REST Framework | 3.15.2 |
| Pytest | 8.3.5 |
| Node.js | 22.23.2 |
| npm | 10.9.8 |
| Rust/Cargo | Missing |
| Tauri CLI | 2.11.4, installed locally |
| Docker/Compose | Missing |
| PostgreSQL client | Missing |
| Redis client | Missing |
| Frontend dependencies | Present in `apps/web/node_modules` |
| Backend dependencies | Imports available from `.venv` |

## Commands and results

| Command | Result | Output summary / notes |
| --- | --- | --- |
| `powershell.exe -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1` | PASS | Required toolchain available; optional Rust, Docker, PostgreSQL, and Redis checks reported missing. |
| `.\.venv\Scripts\python.exe apps\api\manage.py check` | PASS | No issues. |
| `.\.venv\Scripts\python.exe apps\api\manage.py migrate --check` | PASS | No unapplied migrations. |
| `.\.venv\Scripts\python.exe apps\api\manage.py makemigrations --check --dry-run` | PASS | No model changes detected. |
| `.\.venv\Scripts\python.exe apps\api\manage.py test` | PASS | 5 tests found and passed. Covers authentication/CSRF, isolation, evidence hashing, mismatch failure, processing, provenance, and audit. |
| `powershell.exe -ExecutionPolicy Bypass -File .\scripts\run_backend_tests.ps1` | PASS | Django: 5 passed; worker pytest: 2 passed. |
| `.\.venv\Scripts\ruff.exe check apps services` | PASS | No lint errors. |
| `.\.venv\Scripts\ruff.exe format --check apps services` | PASS | 61 files formatted. |
| `npm.cmd run lint` | PASS | TypeScript check passed. |
| `npm.cmd run test` | PASS | 1 test passed in 1 file. |
| `npm.cmd run build` | PASS | Current React/Vite source built successfully. |
| `npm.cmd run format:check` | PASS | Prettier passed. |
| `npm.cmd run e2e` | PASS with scope note | 1 login-screen test passed. The Vite proxy logged expected API connection refusals because no API server was started by the E2E command. |
| `npm.cmd run tauri -- --version` | PASS | Tauri CLI 2.11.4. |
| `npm.cmd run tauri info` | BLOCKED | WebView2 present; Rust/Cargo and MSVC/Windows SDK missing. |
| `npm.cmd run tauri build` | BLOCKED | `cargo metadata` could not run because Cargo is not installed. |
| `.\.venv\Scripts\python.exe scripts\validate_mermaid.py` | PASS | 12 Mermaid source documents validated. |
| Docker Compose PostgreSQL/Redis run | BLOCKED | Docker is not installed; services were not claimed as tested. |

## Passed checks

- Root-safe Django test discovery and backend execution.
- Django system checks, migration checks, backend linting, and formatting.
- Authentication behavior, CSRF-protected login, case isolation, evidence registration, SHA-256 verification, mismatch handling, processing success/failure, provenance creation, audit creation, and worker hashing behavior.
- Frontend TypeScript, unit test, current-source build, formatting, and login-screen E2E check.
- Tauri manifest parsing was repaired; the CLI and configuration can be inspected.
- All 12 Mermaid source documents have supported diagram headers and embedded Mermaid blocks.

## Failed and blocked checks

- Tauri native build: blocked by missing Rust/Cargo and MSVC/Windows SDK.
- PostgreSQL/Redis/Docker integration: blocked by missing Docker and native clients.
- Mermaid rendering: not run; no Mermaid rendering CLI was installed. Source validation is the authoritative Phase 1 check.
- Full authenticated browser workflow: not automated in the existing E2E suite; only the login screen is currently covered, while backend API tests cover the protected workflow behavior.

## Security observations

- Login now requires a CSRF token, and the frontend sends the token on mutating requests.
- Session authentication, case-level access checks, explicit CORS/CSRF origins, secure cookie flags, security headers, and no raw evidence logging are retained.
- Unreadable evidence verification now creates both a custody event and an audit event.
- The Tauri shell has no filesystem plugin or unrestricted native capability and does not bundle Python.
- `.env.example` contains placeholders only. Production must replace the development secret and configure HTTPS/HSTS deliberately.
- `EVIDENCE_ROOT` remains an optional deployment boundary; it must be set to a restricted external evidence location for team/production use. Local development remains intentionally permissive for synthetic fixtures.

## Scope observations and limitations

No advanced forensic parser, acquisition capability, AI call, autonomous conclusion, court-readiness claim, or unrelated product redesign was added. The frontend documentation now accurately describes custom CSS; Tailwind/shadcn are not installed. Existing generated `dist` output was not used as proof of the build; the current source was built during verification.

## Files changed

Created or directly updated for Phase 1:

- Backend: `apps/api/manage.py`, `apps/api/identity/urls.py`, `apps/api/cases/views.py`, `apps/api/cases/tests.py`, `apps/api/config/settings.py`, `.env.example`.
- Frontend: `apps/web/src/api.ts`.
- Desktop: `apps/desktop/src-tauri/Cargo.toml`, `apps/desktop/src-tauri/build.rs`, `apps/desktop/package.json`, `apps/desktop/package-lock.json`, `apps/desktop/README.md`.
- Scripts: `scripts/check_environment.ps1`, `scripts/run_backend_tests.ps1`.
- Documentation: `README.md`, `CHANGELOG.md`, `docs/12-validation-and-testing.md`, `docs/13-deployment-and-operations.md`, `docs/17-phase-1-verification-report.md`, `docs/18-environment-and-toolchain.md`.
- Formatting: existing Python files under `apps/api` and `services/forensic-worker` were mechanically formatted; no behavior was intentionally changed by that formatting pass.

No original evidence was modified. No unrelated files were deleted. No secrets were added.

## Recommended next step

Install and verify the native team toolchain (Rust/MSVC plus Docker Desktop), then run a PostgreSQL/Redis-backed authenticated end-to-end workflow before expanding V0.1 functionality.
