# Deployment and operations

Local development can use SQLite and eager Celery. Start the API with `.\.venv\Scripts\python.exe apps\api\manage.py runserver` and the worker with `celery -A config worker -l INFO` from `apps/api` when Redis is available. Team deployment should use PostgreSQL, Redis, a process supervisor for API and worker, TLS termination, secret management, backups, restricted evidence storage, metrics, error monitoring, and documented restore tests. Docker topology is recorded in `infra/compose/docker-compose.yml`; Docker, PostgreSQL, and Redis were not available in the Phase 1 verification shell and therefore remain unverified.

Run `powershell.exe -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1` before deployment and record its output with the verification report. Do not treat the Compose file or an existing frontend `dist` directory as proof that those services or the current source build have been verified.
