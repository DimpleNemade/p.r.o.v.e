# Environment and toolchain

## Required

| Tool | Version | For |
| --- | --- | --- |
| Python | 3.12+ | API and worker |
| Node.js + npm | 20+ (22 recommended) | web app |
| Git | recent | source control |

The local **SQLite** database and **eager Celery** mode are sufficient for the full
browser workflow and all tests — no database server or broker required.

## Optional

| Tool | Needed only for |
| --- | --- |
| PostgreSQL + Redis | team mode and asynchronous processing |
| Docker + Compose | running the `infra/compose` topology |
| Rust + Cargo, MSVC / platform build tools | building the Tauri desktop shell |
| Mermaid CLI | rendering diagrams to SVG/PNG (the repo validator checks source without it) |

## Reference environment

The versions the scaffold was built and first verified against (2026-08-19):

| Component | Version |
| --- | --- |
| Django | 5.1.11 |
| Django REST Framework | 3.15.2 |
| Celery | 5.5.3 |
| Python | 3.12.4 |
| Node.js | 22.23.2 |
| npm | 10.9.8 |
| React | 18.3.1 |
| Vite | 6.4.3 |
| TypeScript | 5.9.3 |

Backend dependencies are pinned in `apps/api/requirements.txt`; frontend in
`apps/web/package-lock.json`.

## Install

```bash
# from the repository root
python3 -m venv .venv                       # Windows: py -3.12 -m venv .venv
source .venv/bin/activate                    # Windows PS: .\.venv\Scripts\Activate.ps1
pip install -r apps/api/requirements.txt
cd apps/web && npm install && cd ../..
# optional desktop deps
cd apps/desktop && npm install && cd ../..
```

On Windows, install optional tooling with `winget`, e.g.
`winget install OpenJS.NodeJS.LTS`, `winget install Rustlang.Rustup`,
`winget install Docker.DockerDesktop` (a restart may be needed after Rustup or Docker).
On macOS use Homebrew; on Linux use the distribution package manager. Do not install
PostgreSQL or Redis substitutes solely to satisfy an environment check.

## Environment check script (Windows helper)

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1
```

Reports required and optional tools separately, prints no secrets or environment
values, and exits non-zero when a required check fails.

## Platform notes

- The **browser app is the supported path.** The Tauri shell needs Rust/Cargo and
  platform build tools and is otherwise unverified.
- PostgreSQL/Redis/Docker are not "verified" just because the Compose file exists — they
  must be available and exercised in a separate infrastructure run.
- Production must replace the development `SECRET_KEY` and enable HTTPS/HSTS explicitly.
