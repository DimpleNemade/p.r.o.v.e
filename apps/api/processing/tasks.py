from pathlib import Path
from django.utils import timezone
from celery import shared_task
from audit.models import AuditEvent
from evidence.services import calculate_sha256
from .models import ProcessingJob, ProcessingRun
from investigations.models import Artifact, TimelineEvent, ProvenanceLink


@shared_task
def process_evidence_job(job_id):
    job = ProcessingJob.objects.select_related("case", "evidence").get(pk=job_id)
    evidence = job.evidence
    job.status = "running"
    job.save(update_fields=["status", "updated_at"])
    run = ProcessingRun.objects.create(
        case=job.case, job=job, processor_name="basic-metadata", processor_version="0.1.0"
    )
    warnings = []
    try:
        path = Path(evidence.original_path)
        if not path.is_file():
            raise FileNotFoundError("Evidence path is not readable")
        actual = calculate_sha256(str(path))
        size = path.stat().st_size
        if evidence.expected_hash and evidence.expected_hash.lower() != actual:
            evidence.calculated_hash = actual
            evidence.verification_status = "mismatch"
            evidence.save(update_fields=["calculated_hash", "verification_status", "updated_at"])
            raise ValueError("SHA-256 mismatch; processing stopped")
        evidence.calculated_hash = actual
        evidence.verification_status = "verified"
        evidence.save(update_fields=["calculated_hash", "verification_status", "updated_at"])
        artifact = Artifact.objects.create(
            case=job.case,
            source_evidence=evidence,
            source_path=str(path),
            source_hash_reference=actual,
            processing_run=run,
            processor_name=run.processor_name,
            processor_version=run.processor_version,
            content={"name": path.name, "sizeBytes": size, "suffix": path.suffix.lower()},
            limitations=["Basic metadata only; no complete forensic parser was used."],
            warnings=warnings,
        )
        TimelineEvent.objects.create(
            case=job.case,
            artifact=artifact,
            observed_at=timezone.now(),
            event_type="file_registered",
            summary=f"Basic metadata recorded for {path.name}",
            interpretation_status="observed",
        )
        ProvenanceLink.objects.create(
            case=job.case,
            source_evidence=evidence,
            artifact=artifact,
            relationship="derived_from",
            rationale="Created by the basic metadata processor after SHA-256 verification.",
        )
        run.status = "succeeded"
        run.finished_at = timezone.now()
        run.warnings = warnings
        run.save(update_fields=["status", "finished_at", "warnings"])
        job.status = "succeeded"
        job.save(update_fields=["status", "updated_at"])
        AuditEvent.objects.create(
            case=job.case,
            actor=job.requested_by,
            action="processing.completed",
            object_type="ProcessingJob",
            object_id=str(job.id),
            metadata={
                "artifact_id": str(artifact.id),
                "processor": run.processor_name,
                "version": run.processor_version,
            },
        )
        return {"status": "succeeded", "artifact_id": str(artifact.id)}
    except Exception as exc:
        run.status = "failed"
        run.finished_at = timezone.now()
        run.errors = [str(exc)]
        run.save(update_fields=["status", "finished_at", "errors"])
        job.status = "failed"
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        AuditEvent.objects.create(
            case=job.case,
            actor=job.requested_by,
            action="processing.failed",
            object_type="ProcessingJob",
            object_id=str(job.id),
            metadata={"error": str(exc)[:200]},
        )
        return {"status": "failed", "error": str(exc)}
