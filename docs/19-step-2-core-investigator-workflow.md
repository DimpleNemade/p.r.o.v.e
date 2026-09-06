# Step 2 — Core investigator workflow

## Outcome

Step 2 makes the core investigator journey runnable end to end on synthetic fixtures:

`login → case list → case → evidence detail → verify → process → artifact detail → provenance → timeline → finding/support → report preview → audit`

The web application keeps the examiner in control. Processing produces normalized,
clearly labelled derived records; it does not produce an autonomous conclusion. Reports
are development drafts and the export endpoint remains a placeholder.

## API contract

`/api/v1/` is canonical. `/api/` remains as a compatibility alias. All data routes use
session authentication, CSRF for mutations, and case-level read/write authorization.
Detail routes return explicit `404` responses. Cross-case support references are rejected.

The key prerequisite is integrity: `POST /api/v1/evidence/{id}/verify/` calculates SHA-256
against the registered source reference. Only `verified` evidence can be submitted to
`POST /api/v1/cases/{id}/jobs/`; unverified, mismatched, or unreadable evidence returns
`409 integrity_required` and records `processing.blocked`.

## Traceability contract

- Evidence detail exposes expected/calculated hashes, read-only state, custody, warnings,
  and limitations; raw evidence bytes are never returned.
- Artifact detail exposes source evidence, processing run, processor/version, source hash
  reference, limitations, timeline events, related findings, and provenance links.
- A finding has an explicit basis (`observed` or `interpreted`) and can cite one artifact
  or one timeline event per support record.
- A report is a JSON snapshot containing the evidence register, integrity counts,
  processing summary, findings, supports, provenance, timeline, audit count, and
  limitations. It is labelled as a development draft and not court-ready.
- Audit events include case actions plus global login/logout events. Audit, custody, and
  provenance have no update or delete routes.

## Seeded journey

`seed_demo` is safe to run repeatedly and creates `DEMO-0001` with three synthetic
evidence files, three verified hashes, three processing runs, three artifacts, timeline
events, provenance links, one draft finding with support, one report draft, and audit
history. The fixture labels, warnings, and limitations are intentionally visible in the
UI and report preview.

## Acceptance evidence

- Django tests cover authorization, integrity blocking, detail routes, support validation,
  report snapshot serialization, and seed completeness.
- Vitest covers rendered frontend behaviour; Playwright covers the authenticated journey
  with an automatically started API and seeded database.
- `scripts/validate_mermaid.py` checks all documentation Mermaid fences and headers.

## Deliberate boundary

This step does not add acquisition, broad filesystem/mobile/cloud/memory/network parsers,
AI conclusions, signing, legal admissibility, or a real export package. Those require
separate validation, threat modelling, and operational decisions.
