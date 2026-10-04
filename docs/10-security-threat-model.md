# Security threat model

| Threat | Implemented control | Residual assumption |
| --- | --- | --- |
| Cross-case disclosure/write | account-and-membership policy, scoped querysets, FK and nested-boundary validation | trusted DB schema and correctly assigned memberships |
| Arbitrary server-file read | case-relative root, fail-closed path forms, symlink/reparse/special-file rejection | approved root and host permissions are configured correctly |
| Concurrent evidence change | one bounded open handle, immutable bytes, identity/size/time comparisons | complete race elimination needs filesystem snapshots/immutable storage |
| Blank hash presented as authentic | pending state plus separate reasoned acceptance | operator reference provenance remains a human responsibility |
| Duplicate/partial processing | constrained request identity, atomic claim/output commit, preserved attempts | PostgreSQL/real broker gate must pass before team readiness |
| Malicious processor input | no-network restricted child and resource limits, fail-closed team mode | Linux namespace policy and adapter dependencies form trusted computing base |
| Self-approval/stale review | author separation, frozen snapshots, optimistic version check | account identities and role assignment are trusted |
| History modification/tail deletion | canonical chain, record binding, external checkpoint verification | DB administrator can rewrite local history; external checkpoint retention required |
| Malformed export | no extraction, strict allowlist/schema/reference/hash/size/path/duplicate checks | unsigned package does not authenticate author |
| Credential guessing/log leakage | bounded cache limiter, credential-free failure logs | reverse proxy and centralized monitoring should add deployment limits |

See the maintained [risk register](phase3/risk-register.md). P.R.O.V.E. does not claim
forensic parser validation, legal admissibility, compliance certification or production
readiness.
