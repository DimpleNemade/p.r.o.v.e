from pathlib import Path
import sys
import pytest
from django.core.management import call_command
from django.conf import settings
from cases.models import Case
from processing.models import ProcessingJob

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from worker import process_registered_job


@pytest.mark.django_db
def test_registered_job_redelivery_preserves_results():
    call_command("seed_demo")
    case = Case.objects.get(reference="DEMO-PHASE3-0001")
    job = case.processing_jobs.first()
    before = case.artifacts.count()
    result = process_registered_job(job.pk)
    assert result["status"] == "succeeded"
    assert result["redelivery"] is True
    assert case.artifacts.count() == before


@pytest.mark.django_db
def test_changed_registered_input_fails_shared_integrity_boundary():
    call_command("seed_demo")
    case = Case.objects.get(reference="DEMO-PHASE3-0001")
    evidence = case.evidence_items.first()
    (Path(settings.EVIDENCE_ROOT) / str(case.pk) / evidence.original_path).write_bytes(b"changed")
    job = ProcessingJob.objects.create(case=case, evidence=evidence, requested_by=case.owner)
    result = process_registered_job(job.pk)
    assert result["status"] == "failed"
    evidence.refresh_from_db()
    assert evidence.verification_status == "mismatch"
    assert not job.runs.filter(status="succeeded").exists()
