# Security threat model

Trust boundaries are the browser, API, database, queue, worker, and evidence storage. Key threats are unauthorized case access, path traversal or arbitrary path exposure, hash mismatch, sensitive logging, replayed sessions, and worker failure. Mitigations include case membership checks, configured evidence roots, no raw-content logging, secure cookies, CSRF, explicit CORS, append-only records, and safe error messages.

Remaining risks include deployment secrets, OS-level evidence storage permissions, operational backup policy, dependency supply chain, and incomplete production hardening. Run dependency audits before deployment.
