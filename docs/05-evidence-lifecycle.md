# Evidence lifecycle and storage boundary

1. **Register:** an authorized investigator records a relative logical locator under
   `<EVIDENCE_ROOT>/<case UUID>/`, optional SHA-256 reference, and safe acquisition
   context. Registration creates custody and audit records atomically.
2. **Observe:** the service rejects absolute, drive-relative, UNC/device, traversal,
   reserved, alternate-stream, symlink/junction/reparse and non-regular inputs. It opens
   the file read-only, enforces the size limit, captures identity/size/times and reads one
   immutable snapshot. Every result becomes an `EvidenceHash` observation.
3. **Compare:** a matching operator reference becomes the fixed processing baseline.
   Without an external reference the result is `baseline_pending`, not verified.
4. **Accept local baseline:** a separate action requires actor and reason and records the
   limitation that local acceptance does not verify acquisition authenticity.
5. **Process:** every run compares the fresh observation with the accepted baseline.
   Mismatch/unreadable input blocks output and preserves the baseline and new observation.

States are `unverified`, `baseline_pending`, `baseline_accepted`, `verified`, `mismatch`
and `unreadable`. Only SHA-256 with a 64-character hexadecimal digest is accepted.
Legacy absolute paths remain in storage for history but are redacted and must be relocated
through an operator-controlled custody procedure. No migration silently hashes,
relocates, accepts or changes evidence.

See the [evidence state diagram](diagrams/19-phase3-trust-and-workflows.md#evidence-states).
