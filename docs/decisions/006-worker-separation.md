# ADR-006: Separate Python forensic worker

Status: accepted.

Processing is isolated from request handling so hashing and future parser adapters can scale, fail, and be governed separately. The worker writes structured results and provenance, never original evidence.
