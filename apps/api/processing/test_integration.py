import os
import unittest
import threading
import time
from pathlib import Path

from celery.contrib.testing.worker import start_worker
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import TransactionTestCase, skipUnlessDBFeature

from audit.services import append_event, verify_case
from cases.models import Case, CaseParticipant
from evidence.models import EvidenceItem
from evidence.services import observe
from investigations.models import Artifact
from processing.models import ProcessingJob
from processing.services import submit
from processing.tasks import process_evidence_job
from config.celery import app as celery_app


class TeamIntegrationTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("PROVE_INTEGRATION") != "1":
            raise unittest.SkipTest(
                "Set PROVE_INTEGRATION=1 with PostgreSQL, Redis, worker and bubblewrap"
            )
        super().setUpClass()

    def setUp(self):
        self.user = get_user_model().objects.create_user("integration", role="investigator")
        self.case = Case.objects.create(
            reference="PG-INTEGRATION", title="Integration", owner=self.user
        )
        CaseParticipant.objects.create(case=self.case, user=self.user, permission="owner")
        root = Path(settings.EVIDENCE_ROOT) / str(self.case.pk)
        root.mkdir(parents=True, exist_ok=True)
        (root / "known.bin").write_bytes(b"known integration input")
        self.evidence = EvidenceItem.objects.create(
            case=self.case,
            registered_by=self.user,
            display_name="known.bin",
            original_path="known.bin",
            is_synthetic=True,
        )
        observe(self.evidence, self.user)
        from evidence.services import accept_baseline

        accept_baseline(self.evidence, self.user, "Known integration fixture")

    @skipUnlessDBFeature("has_select_for_update")
    def test_postgresql_concurrent_ledger_appends(self):
        failures = []

        def append(index):
            try:
                close_old_connections()
                append_event(self.case, self.user, f"integration.concurrent.{index}")
            except Exception as exc:
                failures.append(exc)
            finally:
                close_old_connections()

        threads = [threading.Thread(target=append, args=(index,)) for index in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(failures, [])
        self.case.refresh_from_db()
        result = verify_case(self.case)
        self.assertTrue(result["valid"], result)

    def test_real_broker_worker_and_duplicate_delivery(self):
        with start_worker(
            celery_app,
            perform_ping_check=False,
            concurrency=1,
            pool="solo",
            loglevel="WARNING",
        ):
            job = submit(self.evidence, self.user, request_key="broker-integration")
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                job.refresh_from_db()
                if job.status in {"succeeded", "failed"}:
                    break
                time.sleep(0.1)
        self.assertEqual(job.status, "succeeded", job.error_message)
        before = Artifact.objects.filter(processing_run__job=job).count()
        results = []
        threads = [
            threading.Thread(target=lambda: results.append(process_evidence_job(str(job.pk))))
            for _ in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(Artifact.objects.filter(processing_run__job=job).count(), before)
        self.assertTrue(all(result.get("redelivery") for result in results))
