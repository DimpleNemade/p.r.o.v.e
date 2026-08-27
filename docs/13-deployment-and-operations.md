# Deployment and operations

## Local development

SQLite + eager Celery, no broker required.

```bash
python apps/api/manage.py migrate
python apps/api/manage.py seed_demo
python apps/api/manage.py runserver
# separate terminal
cd apps/web && npm run dev
```

## Team mode

```bash
docker compose -f infra/compose/docker-compose.yml up -d postgres redis
# .env: DATABASE_URL=postgresql://forensic:forensic@localhost:5432/forensic
#       CELERY_TASK_ALWAYS_EAGER=False
python apps/api/manage.py migrate
cd apps/api && celery -A config worker -l INFO
```

## Production checklist

| Area | Requirement |
| --- | --- |
| Runtime | API and worker under a process supervisor (systemd, supervisord, container orchestrator) |
| Database | PostgreSQL with backups and a **tested** restore |
| Broker | Redis, monitored |
| TLS | termination in front of the API; set `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` |
| Secrets | replace the development `SECRET_KEY`; manage via a secrets store, never `.env` in the image |
| Config | `DEBUG=False`; pass `manage.py check --deploy` |
| Evidence storage | restricted OS permissions; set `EVIDENCE_ROOT` to a controlled location |
| Observability | metrics, error monitoring, and log shipping (never raw evidence) |
| Recovery | documented and rehearsed restore and rollback |

## Verified vs unverified

The Compose file records the intended PostgreSQL/Redis topology; it was **not** exercised
in the Phase 1 verification environment and is therefore unverified. A pre-built
frontend `dist/` is not proof the current source builds. Run
`scripts/check_environment.ps1` (or the equivalent checks) and keep the output with the
verification record.

Related: [10 Deployment topology](diagrams/10-deployment-topology.md) ·
[18 Environment & toolchain](18-environment-and-toolchain.md).
