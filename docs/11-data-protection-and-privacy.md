# Data protection and privacy

## What V0.1 stores

Case metadata, evidence **references and hashes** (not contents), structured artifact
metadata, and examiner-entered text (notes, findings, report drafts). Raw evidence
contents are never read into the database or returned by the API.

## What the operator must decide before real cases

The scaffold does not set policy. Before any non-synthetic evidence, the deploying
organisation must define and document:

- **Lawful basis and purpose** for processing the case data.
- **Retention schedules**, legal hold, archival, and controlled deletion — and confirm
  deletion propagates to any derived store or backup.
- **Access review** cadence for case participants and administrators.
- **Encryption** in transit and at rest, with key ownership and rotation.
- **Backup encryption** and tested restore.
- **Incident response** for suspected exposure or integrity loss.
- **Data minimisation** — limit what is extracted, displayed, and exported by default.

## Design posture

- Access to authoritative and derived data is governed by case membership and role.
- Custody and audit trails support an accountability record (who accessed what, when).
- No external transmission of case material occurs in V0.1; adding any requires an
  explicit governance decision (see [14 AI governance boundary](14-ai-governance-boundary.md)).

This document is not legal advice and does not certify compliance with any jurisdiction.
Development and demos must use synthetic data only.

Related: [10 Security threat model](10-security-threat-model.md).
