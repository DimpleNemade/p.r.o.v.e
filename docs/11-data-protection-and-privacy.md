# Data protection and privacy notes

Evidence and investigation data are sensitive by design. Deployments must define lawful
basis, jurisdiction, retention, disclosure, subject-rights handling and incident response
with qualified advisers; this project asserts none of those decisions.

P.R.O.V.E. keeps original evidence outside the database and excludes it from exports by
default. API and package locators are logical; legacy absolute paths are redacted. The
package allowlist excludes arbitrary acquisition/audit metadata, file identity, private
storage paths, credentials and unrelated cases. Processing errors included in a package
are generalized. Authentication failure logging contains an address digest only.

Database, evidence and output backups must be encrypted, access controlled, restored as a
consistent set and destroyed under the deployment retention policy. Redis must remain
private and carry orchestration data only. Access logs, checkpoints and downloaded
packages can themselves be sensitive and need their own retention/access controls.
