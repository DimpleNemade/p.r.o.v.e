# Validation and testing

**Verification** here means "the software does what we built it to do." It is **not**
validation of forensic parser correctness against ground truth — that is future work
governed by the programme's validation plan.

## Backend

Target coverage: system checks, models, authentication, case isolation, hashing,
mismatch handling, provenance creation, audit creation, API behaviour, worker
success/failure, and permissions.

```bash
# from the repository root
python apps/api/manage.py check
python apps/api/manage.py makemigrations --check --dry-run
python apps/api/manage.py test          # discovers the cases app suite
python -m pytest services/forensic-worker/tests
```

The current `apps/api/cases/tests.py` covers: unauthenticated rejection, CSRF-protected
login, case isolation for a non-participant, evidence hash + processing producing an
artifact and provenance and audit events, and hash mismatch causing the job to fail.

Windows convenience wrappers: `scripts/check_environment.ps1` (toolchain report),
`scripts/run_backend_tests.ps1` (Django suite then worker suite, with counts).

## Frontend

```bash
cd apps/web
npm run lint         # tsc --noEmit
npm run test         # vitest
npm run build
npm run format:check
npm run e2e           # playwright
```

The E2E suite currently checks only the login screen and does not need a live API. Full
authenticated workflow coverage requires the API and a seeded database running, and is
an open item.

## Diagrams

```bash
python scripts/validate_mermaid.py
```

Checks that every `docs/**/*.md` Mermaid block has a supported header **and a balanced
closing fence**.

## Honest status

- Backend: a small but real suite covering the security- and provenance-critical paths.
- Frontend: placeholder coverage; the component test does not yet render the app.
- E2E: login only.
- No ground-truth corpus, differential testing, or timestamp-semantics tests yet.

See [19 Phase 0 gap analysis](19-phase-0-gap-analysis.md) and
[17 Phase 1 verification report](17-phase-1-verification-report.md).
