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
artifact and provenance and audit events, hash mismatch blocking processing, and the
versioned detail/support/report/audit workflow against the seeded synthetic case.

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

The Playwright suite starts the API and Vite dev server, seeds the database, and checks
login → case → evidence verify → process → artifact/provenance → finding/support → report
preview → audit. It intentionally exercises synthetic data only.

## Diagrams

```bash
python scripts/validate_mermaid.py
```

Checks that every `docs/**/*.md` Mermaid block has a supported header **and a balanced
closing fence**.

## Honest status

- Backend: a small but real suite covering the security- and provenance-critical paths.
- Frontend: login rendering and API interaction are covered by Vitest; the main journey is
  covered by Playwright.
- E2E: authenticated core investigator journey passes locally.
- No ground-truth corpus, differential testing, or timestamp-semantics tests yet.

See [19 Phase 0 gap analysis](19-phase-0-gap-analysis.md) and
[17 Phase 1 verification report](17-phase-1-verification-report.md).
