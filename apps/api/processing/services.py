import hashlib
import json
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError, PermissionDenied
from audit.services import append_event
from cases.permissions import allowed
from .models import ProcessingJob

PROCESSOR = "basic-metadata"
VERSION = "0.3.0"
SCHEMA = "prove.metadata/1"


def fingerprint(evidence, parameters):
    value = {
        "case": str(evidence.case_id),
        "evidence": str(evidence.pk),
        "input_sha256": evidence.baseline_hash,
        "processor": PROCESSOR,
        "version": VERSION,
        "parameters": parameters,
        "schema": SCHEMA,
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def publish(job_id):
    from .tasks import process_evidence_job

    ProcessingJob.objects.filter(pk=job_id, status="queued").update(
        publication_attempts=F("publication_attempts") + 1
    )
    try:
        process_evidence_job.delay(str(job_id))
    except Exception:
        ProcessingJob.objects.filter(pk=job_id, status="queued").update(
            publication_status="failed",
            error_message="Broker publication failed; dispatcher retry required",
        )
        return False
    ProcessingJob.objects.filter(pk=job_id).update(publication_status="published")
    return True


def submit(evidence, actor, parameters=None, prior_job=None, reason="", request_key=None):
    if not allowed(actor, evidence.case, "process"):
        raise PermissionDenied("Processing denied")
    if (
        evidence.verification_status not in {"verified", "baseline_accepted"}
        or not evidence.baseline_hash
    ):
        raise ValidationError("Accepted evidence baseline required")
    parameters = parameters or {}
    if parameters != {}:
        raise ValidationError("basic-metadata/0.3.0 accepts no parameters")
    digest = fingerprint(evidence, parameters)
    if prior_job:
        if (
            prior_job.case_id != evidence.case_id
            or prior_job.evidence_id != evidence.pk
            or not reason.strip()
            or not request_key
        ):
            raise ValidationError(
                "Re-examination requires same-case prior job, reason and unique request_key"
            )
        key = "rerun:" + str(request_key)
    else:
        key = "default:" + digest
    if len(key) > 100:
        raise ValidationError("request_key too long")
    with transaction.atomic():
        job, created = ProcessingJob.objects.get_or_create(
            case=evidence.case,
            request_key=key,
            defaults={
                "evidence": evidence,
                "requested_by": actor,
                "fingerprint": digest,
                "parameters": parameters,
                "prior_job": prior_job,
                "reason": reason,
            },
        )
        if not created and (
            job.evidence_id != evidence.pk
            or job.fingerprint != digest
            or job.prior_job_id != getattr(prior_job, "pk", None)
            or job.reason != reason
        ):
            raise ValidationError("Idempotency key conflicts with another request")
        if created:
            append_event(
                evidence.case,
                actor,
                "processing.submitted",
                "ProcessingJob",
                job.pk,
                {
                    "fingerprint": digest,
                    "prior_job": str(prior_job.pk) if prior_job else None,
                    "reason": reason,
                },
            )
            transaction.on_commit(lambda: publish(job.pk))
    return job
