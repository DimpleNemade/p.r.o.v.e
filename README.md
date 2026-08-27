# P.R.O.V.E

**Provenance-first digital forensic investigation platform.**

P.R.O.V.E takes an investigation from acquired evidence to defensible findings without weakening evidential integrity or examiner control. Every artifact, timeline event, finding, and report statement stays linked to its source evidence, the processing that produced it, and the examiner who decided about it.

The name traces the core pipeline:

| | Stage | In the platform |
| --- | --- | --- |
| **P** | Provenance | every artifact and finding links back to source evidence, processor, version, and actor |
| **R** | Register | evidence intake, SHA-256 hashing, and append-only chain of custody |
| **O** | Observe | normalized artifacts, explicitly marked as observations rather than conclusions |
| **V** | Verify | integrity checking; a hash mismatch is blocking and visible |
| **E** | Examine | examiner findings, review states, report drafts, and auditable export |

The V0.1 scaffold supports case management, evidence registration and SHA-256 verification, synthetic processing, artifact search, provenance inspection, examiner findings, audit history, report drafts, and controlled export placeholders.

> This project is a development scaffold. It is not court-ready, production-forensic validated, or a substitute for validated acquisition and parsing tooling.

## Status

V0.1 scaffold. The core workflow, data model, API, browser interface, worker interfaces, tests, and engineering documentation are present. PostgreSQL/Redis/Docker and the Rust/Tauri toolchain are optional local prerequisites and may be unavailable in a workstation environment.

## Workspace

All project files live in `C:\Users\Dimple\Downloads\AA`.

## Architecture

```text
React + TypeScript browser UI ── session-authenticated REST ── Django + DRF API
                                                                      │
                                                            PostgreSQL / SQLite
                                                                      │
                                                            Celery + Redis worker
                                                                      │
                                                        immutable evidence sources
```

The API owns case authorization and provenance records. The worker never mutates original evidence and never logs raw evidence contents. Normalized artifacts are explicitly marked as observations or interpretations; examiner conclusions are separate findings.

## Stack

- Python 3.12+, Django 5.1, Django REST Framework, PostgreSQL, Celery, Redis, drf-spectacular
- React 18, TypeScript, Vite, React Router, TanStack Query, custom CSS, Vitest, Testing Library, Playwright
- Tauri 2 desktop shell (optional; requires Rust/Cargo)

## Quick start

### Environment verification

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1
```

See [`docs/18-environment-and-toolchain.md`](docs/18-environment-and-toolchain.md) for required/optional tools and Windows installation notes.

### Backend

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe apps\api\manage.py migrate
.\.venv\Scripts\python.exe apps\api\manage.py seed_demo
.\.venv\Scripts\python.exe apps\api\manage.py runserver
```

Demo credentials: `admin@example.test` / `ChangeMe-V0.1-only` (development only).

For PostgreSQL set `DATABASE_URL=postgresql://forensic:forensic@localhost:5432/forensic` in `.env`. Without it, development uses `apps/api/db.sqlite3`. For asynchronous jobs set `REDIS_URL=redis://localhost:6379/0`, then run `celery -A config worker -l INFO` from `apps/api`.

### Database and Redis team mode

```powershell
docker compose -f infra\compose\docker-compose.yml up -d postgres redis
Copy-Item .env.example .env
# Set DATABASE_URL and CELERY_TASK_ALWAYS_EAGER=False in .env
.\.venv\Scripts\python.exe apps\api\manage.py migrate
```

Stop services after verification with `docker compose -f infra\compose\docker-compose.yml down`.

### Frontend

```powershell
cd apps\web
npm.cmd install
npm.cmd run dev
```

The Vite proxy sends `/api` to `http://127.0.0.1:8000`.

### Desktop

```powershell
cd apps\desktop
npm.cmd install
npm.cmd run tauri dev
```

This requires Rust/Cargo and Tauri system prerequisites. The web app remains the supported development path when those are unavailable.

## Commands

```powershell
# API from repository root
.\.venv\Scripts\python.exe apps\api\manage.py check
.\.venv\Scripts\python.exe apps\api\manage.py test
.\.venv\Scripts\python.exe apps\api\manage.py makemigrations --check

# Root-safe combined backend verification (Django API tests, then worker tests)
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run_backend_tests.ps1

# Worker tests
.\.venv\Scripts\python.exe -m pytest services\forensic-worker\tests

# Frontend
cd apps\web
npm.cmd run test
npm.cmd run build
npm.cmd run lint
npm.cmd run format:check
npm.cmd run e2e

# Mermaid source validation from repository root
cd ..\..
.\.venv\Scripts\python.exe scripts\validate_mermaid.py

# Build verification
cd apps\web
npm.cmd run build
cd ..\desktop
npm.cmd run tauri build  # requires Rust/Cargo and MSVC/Windows SDK
```

Mermaid sources are under [`docs/diagrams`](docs/diagrams/README.md). Validate with `python scripts/validate_mermaid.py` from the repository root. Docker is optional; `infra/compose/docker-compose.yml` records the intended PostgreSQL/Redis topology. The frontend uses the checked-in custom CSS implementation; Tailwind/shadcn are not installed in V0.1.

## Security and evidence-handling rules

Configuration is environment-based; secrets are excluded from version control. Django session authentication, CSRF protection, secure cookie flags, explicit CORS, password hashing, case-level permissions, security headers, and audit events are enabled or documented. Evidence paths must be explicit, readable, and remain outside application-managed output; original evidence is read-only by policy and no API exposes raw content. Custody, audit, and provenance records are append-only through the application surface.

No external AI calls are made by default. Unsupported evidence is reported as a limitation, not silently parsed. Hash mismatch stops processing and records a failure.

## Scope and limitations

Included: synthetic evidence processing, basic metadata, SHA-256, case workspace, artifacts, timeline, bookmarks, notes, findings, reports, audit, and export placeholder.

Excluded: mobile/live/remote/cloud acquisition, memory forensics, complete parser coverage, autonomous conclusions, threat intelligence, legal claims, destructive evidence operations, graph database, billing, and full student workflows.

## Documentation index

See the numbered documents in [`docs/`](docs/00-programme-overview.md) and the [ADR index](docs/decisions/README.md).

## Troubleshooting

- If `npm` is blocked by PowerShell execution policy, use `npm.cmd`.
- If PostgreSQL or Redis is unavailable, use SQLite synchronous development mode and `CELERY_TASK_ALWAYS_EAGER=True`.
- If Mermaid CLI is unavailable, review source files and run `scripts/validate_mermaid.py`.
- If Tauri cannot build, install Rust/Cargo and platform prerequisites; the browser app remains supported.

## Roadmap and contribution

Validated parser adapters, acquisition integrations, OIDC/MFA, review workflows, signed exports, operational hardening, and training features are future work. Keep domain changes, diagrams, tests, and documentation synchronized. Do not add secrets or raw evidence. Record architectural changes as ADRs. See [`CHANGELOG.md`](CHANGELOG.md) and [`docs/16-glossary.md`](docs/16-glossary.md).
