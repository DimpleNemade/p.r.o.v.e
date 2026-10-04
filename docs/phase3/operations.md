# Phase 3 installation, operations, backup and recovery

## Development and test profiles

Development uses SQLite and eager Celery. Put staged synthetic files at
`var/evidence/<case UUID>/<relative locator>` and private packages under `var/output`.
The browser suite creates a fresh operating-system temporary directory, SQLite database,
evidence root and output root, and reserves API port 8017 and web port 5187. It refuses
to reuse existing servers.

```powershell
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt
$env:PROVE_PROFILE = "development"
.\.venv\Scripts\python.exe apps\api\manage.py migrate
.\.venv\Scripts\python.exe apps\api\manage.py seed_demo
.\.venv\Scripts\python.exe apps\api\manage.py runserver 127.0.0.1:8000
npm.cmd --prefix apps\web install
npm.cmd --prefix apps\web run dev
```

`seed_demo` creates only `DEMO-PHASE3-0001`. If that case already exists it exits without
changing passwords, hashes, job state, findings, reports or audit events. Demo credentials
exist only for accounts created by that command:
`investigator@example.test` and `reviewer@example.test`, both with
`ChangeMe-Phase3-only`. Change them for any retained environment.

## Team profile

Create `.env.team` with `PROVE_PROFILE=team`, a 50+ character nondevelopment secret,
PostgreSQL and Redis URLs, explicit hosts and HTTPS origins, eager mode false, and the
container paths `/var/lib/prove/evidence` and `/var/lib/prove/output`. The team Compose
keeps PostgreSQL/Redis on an internal network, mounts evidence read-only, drops worker
capabilities and provides bounded private output.

```powershell
docker compose -f infra\compose\docker-compose.team.yml build
docker compose -f infra\compose\docker-compose.team.yml run --rm api python manage.py check --deploy
docker compose -f infra\compose\docker-compose.team.yml run --rm api python manage.py migrate --noinput
docker compose -f infra\compose\docker-compose.team.yml up api worker
```

## Backup, migration and restore

1. Stop new processing and wait for running jobs or record them for explicit recovery.
2. Back up PostgreSQL at one consistent point and snapshot the evidence and output
   volumes. Record hashes and access controls for all three. A database-only restore can
   leave packages or evidence locators inconsistent.
3. Test restore into a disposable environment and run `migrate --plan`, `migrate`,
   `check`, `verify_ledger <case-id>`, then one authorized read-only package verification.
4. Apply production migrations. They preserve legacy fields and never accept or replace
   an evidence baseline.
5. If rollback is necessary, restore the complete pre-migration set. Do not reverse the
   checkpoint migration on live history or partially copy rows.

Run `python apps/api/manage.py dispatch_jobs` after a broker outage. Add
`--recover-stale` only after establishing that claimed jobs have exceeded ten minutes and
their workers are gone. Recovery records an interruption and requeues; it never converts
a failed attempt into success.

Retain exported ledger checkpoints in a separately controlled location. Verify backups
periodically; merely creating a backup does not show it can be restored.
