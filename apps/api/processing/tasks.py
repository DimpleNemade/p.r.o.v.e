import hashlib
import json
import platform
import uuid
import django
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from audit.services import append_event
from cases.permissions import allowed
from evidence.services import observe
from investigations.models import Artifact, TimelineEvent, ProvenanceLink
from .models import ProcessingJob, ProcessingRun
from .services import PROCESSOR, VERSION, SCHEMA, fingerprint
from .boundary import run_metadata


@shared_task(acks_late=True, reject_on_worker_lost=True)
def process_evidence_job(job_id):
    token = uuid.uuid4()
    # Conditional UPDATE is an atomic claim on both database engines.
    with transaction.atomic():
        claimed = ProcessingJob.objects.filter(pk=job_id, status="queued").update(
            status="running", claim_token=token, claimed_at=timezone.now()
        )
        if not claimed:
            return {"status": ProcessingJob.objects.get(pk=job_id).status, "redelivery": True}
        job = ProcessingJob.objects.select_related("case", "evidence", "requested_by").get(
            pk=job_id
        )
        run = ProcessingRun.objects.create(
            case=job.case,
            job=job,
            attempt_token=token,
            processor_name=PROCESSOR,
            processor_version=VERSION,
        )
        append_event(
            job.case,
            job.requested_by,
            "processing.started",
            "ProcessingRun",
            run.pk,
            {"attempt": str(token)},
            service="metadata-worker",
        )
    try:
        if job.evidence.case_id != job.case_id or not allowed(
            job.requested_by, job.case, "process"
        ):
            raise ValueError("Processing authorization revoked or case mismatch")
        content, actual, metadata = observe(job.evidence, job.requested_by)
        evidence = job.evidence
        if (
            not evidence.baseline_hash
            or actual != evidence.baseline_hash
            or evidence.verification_status not in {"verified", "baseline_accepted"}
        ):
            raise ValueError("Accepted input baseline comparison failed")
        output = run_metadata(content, evidence.is_synthetic)
        if output["sha256"] != actual:
            raise ValueError("Child input digest differs from accepted snapshot")
        output_digest = hashlib.sha256(
            json.dumps(output, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with transaction.atomic():
            current = ProcessingJob.objects.select_for_update().get(pk=job.pk)
            if current.claim_token != token or current.status != "running":
                return {"status": "superseded_attempt"}
            if not allowed(job.requested_by, job.case, "process"):
                raise ValueError("Processing authorization revoked")
            evidence.refresh_from_db()
            if evidence.baseline_hash != actual or evidence.verification_status not in {
                "verified",
                "baseline_accepted",
            }:
                raise ValueError("Evidence integrity changed before output commit")
            run.reproducibility = {
                "input_sha256": actual,
                "fingerprint": fingerprint(evidence, job.parameters),
                "parameters": job.parameters,
                "schema": SCHEMA,
                "python": platform.python_version(),
                "django": django.get_version(),
                "output_sha256": output_digest,
                "file_identity": metadata,
                "execution": "restricted-team"
                if not evidence.is_synthetic
                else "synthetic-development or restricted-team",
            }
            artifact = Artifact.objects.create(
                case=job.case,
                source_evidence=evidence,
                source_path=evidence.original_path,
                source_hash_reference=actual,
                processing_run=run,
                processor_name=PROCESSOR,
                processor_version=VERSION,
                content=output,
                limitations=[
                    "Basic metadata only; source-event time unknown; no forensic parser validation."
                ],
            )
            TimelineEvent.objects.create(
                case=job.case,
                artifact=artifact,
                observed_at=None,
                timestamp_meaning="source_time_unknown",
                timestamp_uncertainty="Processor records no source timestamp",
                event_type="metadata_processed",
                summary="Metadata processed; source-event time unknown",
                interpretation_status="normalized",
            )
            link = ProvenanceLink.objects.create(
                case=job.case,
                source_evidence=evidence,
                artifact=artifact,
                relationship="derived_from",
                rationale="Derived from the same accepted-digest snapshot used for integrity comparison.",
            )
            run.status = "succeeded"
            run.finished_at = timezone.now()
            run.save()
            current.status = "succeeded"
            current.error_message = ""
            current.save()
            append_event(
                job.case,
                job.requested_by,
                "processing.completed",
                "ProcessingJob",
                job.pk,
                {
                    "artifact_id": str(artifact.pk),
                    "provenance": str(link.pk),
                    "run": str(run.pk),
                    "output_sha256": output_digest,
                },
                service="metadata-worker",
            )
        return {"status": "succeeded", "artifact_id": str(artifact.pk)}
    except Exception as exc:
        # No paths, process output, credentials or arbitrary exception text in history.
        error = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        with transaction.atomic():
            current = ProcessingJob.objects.select_for_update().get(pk=job.pk)
            if current.claim_token == token and current.status == "running":
                run.status = "failed"
                run.finished_at = timezone.now()
                run.errors = [error]
                run.save()
                current.status = "failed"
                current.error_message = error
                current.save()
                append_event(
                    job.case,
                    job.requested_by,
                    "processing.failed",
                    "ProcessingJob",
                    job.pk,
                    {"error": error, "attempt": str(token)},
                    service="metadata-worker",
                )
        return {"status": "failed", "error": error}
