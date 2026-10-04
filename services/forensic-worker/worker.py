"""Compatibility entrypoint for registered jobs. Storage/integrity live in Django.

The former arbitrary-path processor and fake status/record functions are removed.
Celery orchestration is not the sandbox; processing.boundary enforces the child.
"""


def process_registered_job(job_id):
    from processing.tasks import process_evidence_job

    return process_evidence_job(str(job_id))
