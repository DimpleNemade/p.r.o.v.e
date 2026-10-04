from unittest.mock import patch
from django.test import TestCase, override_settings
from django.conf import settings
from django.core.management import call_command
from cases.models import Case
from audit.models import AuditEvent
from .models import ProcessingJob, ProcessingRun
from .services import submit, publish
from .tasks import process_evidence_job
from .boundary import run_metadata


class ProcessingTests(TestCase):
    def setUp(self):
        call_command("seed_demo")
        self.case = Case.objects.get(reference="DEMO-PHASE3-0001")
        self.evidence = self.case.evidence_items.first()
        self.user = self.case.owner

    def test_redelivery_does_not_duplicate_outputs_or_completion(self):
        job = self.evidence.processing_jobs.first()
        before = (
            self.case.artifacts.count(),
            job.runs.count(),
            self.case.audit_events.filter(action="processing.completed").count(),
        )
        self.assertEqual(process_evidence_job(str(job.pk))["status"], "succeeded")
        self.assertEqual(
            before,
            (
                self.case.artifacts.count(),
                job.runs.count(),
                self.case.audit_events.filter(action="processing.completed").count(),
            ),
        )

    def test_default_request_reuse_and_intentional_reexamination(self):
        with self.captureOnCommitCallbacks(execute=True):
            first = submit(self.evidence, self.user)
        second = submit(self.evidence, self.user)
        self.assertEqual(first.pk, second.pk)
        with self.captureOnCommitCallbacks(execute=True):
            new = submit(
                self.evidence,
                self.user,
                prior_job=first,
                reason="Independent repeat",
                request_key="repeat-1",
            )
        self.assertNotEqual(first.pk, new.pk)
        self.assertEqual(first.fingerprint, new.fingerprint)
        self.assertEqual(new.prior_job_id, first.pk)
        self.assertEqual(
            submit(
                self.evidence,
                self.user,
                prior_job=first,
                reason="Independent repeat",
                request_key="repeat-1",
            ).pk,
            new.pk,
        )

    def test_mid_commit_failure_rolls_back_all_outputs(self):
        job = ProcessingJob.objects.create(
            case=self.case, evidence=self.evidence, requested_by=self.user
        )
        before = self.case.artifacts.count()
        with patch(
            "processing.tasks.ProvenanceLink.objects.create",
            side_effect=RuntimeError("injected failure"),
        ):
            result = process_evidence_job(str(job.pk))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(before, self.case.artifacts.count())
        self.assertFalse(job.runs.filter(status="succeeded").exists())
        self.assertFalse(
            AuditEvent.objects.filter(action="processing.completed", object_id=str(job.pk)).exists()
        )
        self.assertTrue(job.runs.filter(status="failed").exists())

    def test_changed_baseline_blocks_processing_and_retains_observation(self):
        from pathlib import Path

        baseline = self.evidence.baseline_hash
        (
            Path(settings.EVIDENCE_ROOT) / str(self.case.pk) / self.evidence.original_path
        ).write_bytes(b"changed")
        job = ProcessingJob.objects.create(
            case=self.case, evidence=self.evidence, requested_by=self.user
        )
        self.assertEqual(process_evidence_job(str(job.pk))["status"], "failed")
        self.evidence.refresh_from_db()
        self.assertEqual(self.evidence.baseline_hash, baseline)
        self.assertEqual(self.evidence.verification_status, "mismatch")
        self.assertTrue(self.evidence.hashes.filter(status="mismatch").exists())

    def test_publication_failure_is_recoverable_and_not_silent(self):
        job = ProcessingJob.objects.create(
            case=self.case, evidence=self.evidence, requested_by=self.user
        )
        with patch("processing.tasks.process_evidence_job.delay", side_effect=ConnectionError):
            self.assertFalse(publish(job.pk))
        job.refresh_from_db()
        self.assertEqual(job.publication_status, "failed")
        self.assertTrue(publish(job.pk))
        job.refresh_from_db()
        self.assertEqual(job.status, "succeeded")
        self.assertEqual(job.publication_attempts, 2)

    def test_unknown_source_time_and_stored_reproducibility(self):
        for event in self.case.timeline_events.all():
            self.assertIsNone(event.observed_at)
            self.assertEqual(event.timestamp_meaning, "source_time_unknown")
        run = self.evidence.processing_jobs.first().runs.get()
        self.assertEqual(run.reproducibility["input_sha256"], self.evidence.baseline_hash)
        self.assertEqual(len(run.reproducibility["output_sha256"]), 64)

    def test_limits_and_no_team_fallback(self):
        with override_settings(MAX_EVIDENCE_BYTES=1), self.assertRaises(ValueError):
            run_metadata(b"too long", True)
        with self.assertRaises(ValueError):
            run_metadata(b"real evidence", False)
        with (
            override_settings(PROFILE="team"),
            patch("processing.boundary.shutil.which", return_value=None),
            self.assertRaises(ValueError),
        ):
            run_metadata(b"test", True)
