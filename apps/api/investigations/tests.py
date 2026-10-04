from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied, ValidationError
from cases.models import Case, CaseParticipant
from .services import transition, Conflict


class ReviewTests(TestCase):
    def setUp(self):
        call_command("seed_demo")
        self.case = Case.objects.get(reference="DEMO-PHASE3-0001")
        self.finding = self.case.findings.first()
        self.author = self.case.owner
        self.reviewer = get_user_model().objects.get(username="reviewer@example.test")

    def act(self, actor, action, comments="Reviewed supporting records"):
        self.finding.refresh_from_db()
        return transition(self.finding.pk, actor, action, self.finding.version, comments)

    def test_independent_review_and_snapshot_preservation(self):
        self.act(self.author, "submit")
        self.author.role = "administrator"
        self.author.save()
        with self.assertRaises(PermissionDenied):
            self.act(self.author, "start_review")
        self.act(self.reviewer, "start_review")
        self.act(self.reviewer, "approve")
        revision = self.finding.revisions.get()
        snapshot = revision.snapshot
        self.act(self.author, "supersede", "New interpretation")
        revision.refresh_from_db()
        self.assertEqual(revision.status, "approved")
        self.assertEqual(revision.snapshot, snapshot)
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.examiner_status, "draft")

    def test_version_conflict_prevents_overwrite(self):
        old = self.finding.version
        self.act(self.author, "submit")
        with self.assertRaises(Conflict):
            transition(self.finding.pk, self.reviewer, "start_review", old, "stale")

    def test_missing_traceability_blocks_submission(self):
        self.case.provenance_links.all().delete()
        with self.assertRaises(ValidationError):
            self.act(self.author, "submit")
        self.assertFalse(self.finding.revisions.exists())

    def test_later_integrity_failure_blocks_approval(self):
        self.act(self.author, "submit")
        self.act(self.reviewer, "start_review")
        self.case.evidence_items.update(verification_status="mismatch")
        with self.assertRaises(ValidationError):
            self.act(self.reviewer, "approve")
        self.assertFalse(self.finding.revisions.filter(status="approved").exists())

    def test_generic_content_and_support_updates_cannot_inherit_approval(self):
        from rest_framework.test import APIClient

        self.act(self.author, "submit")
        client = APIClient()
        client.force_authenticate(self.author)
        response = client.patch(
            f"/api/v1/findings/{self.finding.pk}/",
            {"finding_text": "changed", "version": self.finding.version},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        response = client.post(
            f"/api/v1/findings/{self.finding.pk}/support/",
            {"artifact": str(self.case.artifacts.first().pk)},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
