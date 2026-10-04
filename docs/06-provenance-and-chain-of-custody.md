# Provenance, custody and verifiable history

Custody records who performed an evidence action. Provenance records which accepted
evidence and processing run produced an artifact. Finding support and report revisions
then bind those stored records; a missing link is returned and displayed as missing.

`prove.audit/1` serializes UTF-8 JSON with sorted keys, compact separators, no NaN and no
Unicode normalization rewrite. Each event binds ID, case, sequence, actor, service,
action, object, time, safe metadata digest, previous hash, and custody/provenance record
digest. Case counter updates and unique `(case, sequence)` prevent duplicate positions.
Business writes and their audit event share a transaction.

`verify_ledger` is read-only: it reports event modification, missing/reordered positions,
record changes and retained-checkpoint mismatch and never repairs history. The Phase 3
migration hashes legacy rows at a dated checkpoint. That is the first binding, not proof
that earlier history was independently trusted.

```powershell
.\.venv\Scripts\python.exe apps\api\manage.py verify_ledger <case-uuid>
.\.venv\Scripts\python.exe apps\api\manage.py verify_ledger <case-uuid> --checkpoint checkpoint.json
```

A local chain cannot defeat an administrator who rewrites records and hashes. Tail
deletion requires a separately retained checkpoint. There is no blockchain or absolute
immutability claim.
