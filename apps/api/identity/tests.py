from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from cases.models import Case


class FixtureTests(TestCase):
    def test_repeated_seed_preserves_password_failure_hash_finding_report_and_user_records(self):
        call_command("seed_demo")
        case = Case.objects.get(reference="DEMO-PHASE3-0001")
        user = get_user_model().objects.get(username="investigator@example.test")
        user.set_password("investigator changed this")
        user.save()
        evidence = case.evidence_items.first()
        evidence.expected_hash = "0" * 64
        evidence.save()
        job = case.processing_jobs.first()
        job.status = "failed"
        job.error_message = "Preserve this"
        job.save()
        finding = case.findings.first()
        finding.finding_text = "Examiner edit"
        finding.save()
        report = case.reports.first()
        report.body = {"preserve": True}
        report.save()
        counts = [case.evidence_items.count(), case.artifacts.count(), case.audit_events.count()]
        call_command("seed_demo")
        user.refresh_from_db()
        evidence.refresh_from_db()
        job.refresh_from_db()
        finding.refresh_from_db()
        report.refresh_from_db()
        self.assertTrue(user.check_password("investigator changed this"))
        self.assertEqual(evidence.expected_hash, "0" * 64)
        self.assertEqual(job.status, "failed")
        self.assertEqual(job.error_message, "Preserve this")
        self.assertEqual(finding.finding_text, "Examiner edit")
        self.assertEqual(report.body, {"preserve": True})
        self.assertEqual(
            counts, [case.evidence_items.count(), case.artifacts.count(), case.audit_events.count()]
        )
