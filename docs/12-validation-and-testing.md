# Validation and testing

Use the exact current commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m ruff check apps\api services scripts
.\.venv\Scripts\python.exe -m ruff format --check apps\api services scripts
.\.venv\Scripts\python.exe -m pip check
Push-Location apps\api; ..\..\.venv\Scripts\python.exe manage.py check --settings=config.test_settings; ..\..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.test_settings; ..\..\.venv\Scripts\python.exe manage.py test --settings=config.test_settings --noinput; Pop-Location
.\.venv\Scripts\python.exe -m pytest services\forensic-worker\tests -q
npm.cmd --prefix apps\web run lint
npm.cmd --prefix apps\web test
npm.cmd --prefix apps\web run format:check
npm.cmd --prefix apps\web run build
npm.cmd --prefix apps\web audit --audit-level=moderate
npm.cmd --prefix apps\web run e2e
npm.cmd --prefix apps\web run diagrams:validate
.\.venv\Scripts\python.exe scripts\verify_package.py <package.zip>
```

The browser launcher always creates isolated database/evidence/output roots, uses ports
8017/5187 and refuses server reuse. Run the suite twice for clean-environment evidence.
Repeated seeding and job redelivery are separately covered in retained test databases.

The `team-integration` CI job runs PostgreSQL concurrency, Redis/Celery and the Linux
restricted child. A workflow file is reproducible configuration; only a completed CI run
is evidence it passed. SQLite/eager mode cannot substitute for that gate.

Tests establish implemented software behavior. They do not establish parser correctness
against forensic ground truth, evidential/legal admissibility or production readiness.
Current results are in the [Phase 3 report](21-phase-3-implementation-verification.md).
