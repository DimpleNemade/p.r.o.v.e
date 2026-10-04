# Deployment and operations

There are three profiles: `development`, `test`, and `team`. Development uses local
SQLite/eager synthetic processing. Test creates dedicated temporary database, evidence
and output roots. Team refuses SQLite, eager Celery, weak/missing secret, wildcard/non-HTTPS
origins, malformed PostgreSQL/Redis URLs and missing/non-disjoint storage.

PostgreSQL and Redis bind only to loopback in the development Compose topology. The team
Compose does not publish them and gives the worker only its internal orchestration network.
Evidence is a read-only volume; output is private and writable. The processing child has
no network namespace.

Deployment still needs a supported reverse proxy/application server, TLS, secret manager,
monitoring, encrypted backup storage, tested restore, checkpoint retention and OS policy.
The included API `runserver` command is a development/integration entrypoint and is not a
production application server.

Detailed startup, backup, migration and recovery procedures are maintained in
[Phase 3 operations](phase3/operations.md). The executable topology is
`infra/compose/docker-compose.team.yml`.
