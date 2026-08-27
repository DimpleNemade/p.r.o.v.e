# Product constitution

The rules the product is not allowed to trade away for convenience or speed. Everything
in the codebase should be checkable against this list.

## Principles

1. **Evidence integrity precedes convenience.** Original evidence is accessed read-only.
   Integrity is verified at registration and on demand, and a mismatch stops work.
2. **Provenance is a first-class record, not UI decoration.** The link from a derived
   record to its source is a stored, queryable relationship
   (`investigations.ProvenanceLink`), not a rendering detail.
3. **Observation is not interpretation.** Observed data, normalized interpretation,
   machine-generated suggestion, and examiner-approved conclusion are distinct states
   (`TimelineEvent.interpretation_status`, `Finding.examiner_status`).
4. **Examiner control is explicit.** Automation organizes and suggests. A competent
   human accepts, rejects, contextualizes, and owns every material conclusion.
5. **Unsupported capability is disclosed, not implied.** Limitations are recorded on the
   artifact and surfaced at the point of use.
6. **Audit and custody are append-only at the application boundary.** No ordinary
   update or delete route exists for `AuditEvent`, `CustodyEvent`, or `ProvenanceLink`.

## Claims discipline

The product, its documentation, and its marketing do **not** assert:

- legal admissibility or "court-ready" status;
- accreditation or certification against any standard;
- complete parser coverage or universal format support;
- autonomous investigative, attribution, or evidential conclusions;
- production-forensic validation.

Permitted framing is "designed to support" and "provides features that support
defensible practice" — never "compliant with" or "validated" without a precise,
documented basis.

## How a change is tested against this document

| Question | If yes |
| --- | --- |
| Does it touch original evidence or alter interpretation? | Treat as release-blocking; requires forensic-impact review. |
| Does it weaken auditability for convenience? | Reject the change. |
| Does it let automation produce a conclusion without examiner sign-off? | Reject the change. |
| Does it send case material outside the controlled environment? | Stop pending an explicit governance decision. |

Related: [02 V0.1 scope](02-v0.1-scope.md) · [ADR-009 provenance-first](decisions/009-provenance-first.md) · [14 AI governance boundary](14-ai-governance-boundary.md).
