# Environment and toolchain

Verification date: 2026-08-19  
Workspace: `C:\Users\Dimple\Downloads\AA`

## Detected environment

| Tool | Detected status |
| --- | --- |
| Windows | Windows host; exact build is emitted by `scripts/check_environment.ps1` |
| Python | 3.12.4 |
| Virtual environment | `.venv` present |
| Django | 5.1.11 |
| Django REST Framework | 3.15.2 |
| Pytest | 8.3.5 |
| Node.js | v22.23.2 |
| npm | 10.9.8 |
| Rust/Cargo | Not available in the verification shell |
| Tauri CLI | Optional desktop dependency; unavailable until desktop npm dependencies are installed |
| Docker / Compose | Not available in the verification shell |
| PostgreSQL client | Not available in the verification shell |
| Redis client | Not available in the verification shell |
| Frontend dependencies | `apps/web/node_modules` present |
| Backend dependencies | Local imports available from `.venv` |

## Required tools

Python 3.12+, a project virtual environment, the pinned backend requirements, Node.js/npm, and the frontend dependencies are required for the browser-supported V0.1 workflow. The local SQLite database and eager Celery mode are sufficient for deterministic development and tests.

## Optional tools

Rust/Cargo and Tauri prerequisites are required only for the desktop shell. Docker Desktop, PostgreSQL, and Redis are required only for team-mode infrastructure verification and asynchronous processing. Mermaid CLI is optional because the repository validator checks the embedded source blocks without rendering.

## Installation

From the workspace root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt
cd apps\web
npm.cmd install
cd ..\..\apps\desktop
npm.cmd install
```

Install optional tooling with the available Windows package manager, for example `winget install Python.Python.3.12`, `winget install OpenJS.NodeJS.LTS`, `winget install Rustlang.Rustup`, and `winget install Docker.DockerDesktop`. Restart may be required after Rustup or Docker Desktop installation. Do not install PostgreSQL or Redis alternatives solely to satisfy this check.

## Rerun the check

PowerShell execution policy may block local `.ps1` files. Run the check without changing the machine policy:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1
```

The script reports required and optional tools separately, does not print environment values or secrets, and returns a non-zero exit code when required checks fail.

## Platform limitations

The browser application is the supported local path. The Tauri shell cannot be verified without Rust/Cargo and MSVC/Windows SDK prerequisites. PostgreSQL/Redis/Docker are not considered verified merely because Compose configuration exists; they must be available and exercised in a separate infrastructure run. Production deployments must replace the development `SECRET_KEY` placeholder and enable HTTPS/HSTS settings explicitly.
