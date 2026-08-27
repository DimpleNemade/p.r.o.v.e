# Forensic worker

The worker is deliberately separate from the API and exposes a small orchestration interface. V0.1 supports SHA-256, readable-path checks, basic file metadata artifacts, provenance links, and safe failure recording. It does not parse complete forensic formats and never writes to original evidence.

The API task in `apps/api/processing/tasks.py` is the Celery adapter used in development. The standalone service boundary below is the future deployment seam.
