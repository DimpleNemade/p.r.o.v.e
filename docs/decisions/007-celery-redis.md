# ADR-007: Celery and Redis for processing jobs

Status: accepted.

Celery and Redis provide a common asynchronous job model with retries and status tracking. Eager execution supports deterministic local development and tests.
