# Phase 3 architecture, controls and privacy

The Django API owns authorization and durable state. PostgreSQL provides team transaction
and concurrency semantics; SQLite is a development convenience. Redis/Celery carries job
identity only. Evidence bytes cross the case storage boundary into one bounded immutable
snapshot, then into a restricted metadata child. Derived records return to the API and
private packages go to the output root. See the eight current
[trust and workflow diagrams](../diagrams/19-phase3-trust-and-workflows.md).

The storage locator and filesystem path are deliberately separate concepts. Public API
and export fields contain relative locators; legacy/private paths are redacted. Evidence
content, credentials, arbitrary metadata, raw exception strings and unrelated case rows
are excluded from packages. Database `read_only` records application intent and are not
presented as operating-system enforcement.

The permission decision is `account capability ∩ case membership`. Read requires any
membership. Evidence, processing, finding, reporting and export require `owner` or `edit`
membership plus the named role capability. Review requires `owner` or `review` membership
plus reviewer capability. Participant management requires the consistent case owner.
Normal application review never permits the finding author to approve, including an
administrator.

| Account role | Create case | Participants | Evidence/process/finding | Review | Report/export |
| --- | --- | --- | --- | --- | --- |
| administrator | yes | owner membership | owner/edit membership | owner/review membership, independent only | owner/edit membership |
| supervisor | yes | owner membership | owner/edit membership | owner/review membership, independent only | owner/edit membership |
| investigator | yes | owner membership | owner/edit membership | no | owner/edit membership |
| reviewer | no | no | no | owner/review membership, independent only | no |
| auditor | no | no | no | no | no |
| student | no | no | owner/edit membership | no | no |

Case owner and owner membership are created atomically. Ordinary participant APIs cannot
grant ownership or remove participants; therefore they cannot create a second owner or
remove the last owner. Any future transfer/removal endpoint must lock the case and retain
at least one account with owner consistency.

Audit trust is tamper evidence under restricted database administration, not absolute
immutability. Package checksums are consistency evidence, not identity proof. Sensitive
case data still requires least-privilege host access, encryption and retention controls.
No legal or standards applicability is asserted.
