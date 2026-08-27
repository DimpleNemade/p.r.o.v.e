# Glossary

Terms are used consistently across the code, API, and documentation.

| Term | Meaning |
| --- | --- |
| **Artifact** | a normalized record derived from registered evidence by a processing run |
| **Chain of custody** | the chronological record of controlled actions on an item of evidence (`CustodyEvent`) |
| **Provenance** | the stored, queryable relationship between source evidence and a derived record (`ProvenanceLink`) |
| **Processing job / run** | a request to process evidence (`ProcessingJob`) and one execution of a named, versioned processor (`ProcessingRun`) |
| **Verification** | computing SHA-256 of evidence and comparing it to the expected value; a mismatch is blocking |
| **Finding** | an examiner-authored statement with explicit supporting sources and a review state |
| **Finding support** | a link from a finding to an artifact or timeline event that backs it |
| **Report draft** | a snapshot assembled from a case's findings and provenance; not a signed report |
| **Export package** | the intended reproducibility bundle (identifiers, hashes, versions, sources, limitations); a placeholder in V0.1 |
| **Observed evidence** | a directly recorded source fact — not an examiner conclusion |
| **Normalized interpretation** | a structured representation produced by a processor |
| **Machine-generated suggestion** | a future, labelled output that requires examiner review; not produced by V0.1 |
| **Examiner-approved conclusion** | a human-controlled finding status; never produced automatically |
| **Case participant** | a user granted access to a case at a permission level (owner/edit/review/read) |
| **Eager mode** | Celery running tasks inline (`CELERY_TASK_ALWAYS_EAGER`), so the workflow runs without a broker |
