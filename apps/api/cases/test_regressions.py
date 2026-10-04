"""Behavior regressions also run against archived 537309e before fixes."""

import hashlib
import tempfile
from pathlib import Path
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from cases.models import Case, CaseParticipant
from evidence.models import EvidenceItem
from investigations.models import Artifact, Finding, Bookmark, InvestigatorNote
from processing.models import ProcessingJob, ProcessingRun


class AccessRegressions(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("author", role="investigator")
        self.case = Case.objects.create(reference="R1", title="Case", owner=self.user)
        self.other = Case.objects.create(reference="R2", title="Other", owner=self.user)
        CaseParticipant.objects.create(case=self.case, user=self.user, permission="edit")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.finding = Finding.objects.create(
            case=self.case, author=self.user, finding_text="Draft"
        )

    def test_generic_patch_cannot_self_approve(self):
        for prefix in ("/api", "/api/v1"):
            result = self.client.patch(
                f"{prefix}/findings/{self.finding.pk}/",
                {"examiner_status": "approved", "review_status": "reviewed"},
                format="json",
            )
            self.assertEqual(result.status_code, 400)
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.examiner_status, "draft")

    def test_generic_patch_cannot_move_case(self):
        result = self.client.patch(
            f"/api/v1/findings/{self.finding.pk}/", {"case": str(self.other.pk)}, format="json"
        )
        self.assertEqual(result.status_code, 400)
        self.finding.refresh_from_db()
        self.assertEqual(self.finding.case_id, self.case.pk)

    def test_editor_cannot_grant_owner(self):
        target = get_user_model().objects.create_user("target")
        result = self.client.post(
            f"/api/v1/cases/{self.case.pk}/participants/",
            {"user": str(target.pk), "permission": "owner"},
            format="json",
        )
        self.assertEqual(result.status_code, 403)
        self.assertFalse(CaseParticipant.objects.filter(user=target).exists())

    def test_readonly_account_cannot_create_case(self):
        self.user.role = "auditor"
        self.user.save()
        result = self.client.post("/api/v1/cases/", {"reference": "ESCAPE", "title": "Denied"})
        self.assertEqual(result.status_code, 403)

    def test_readonly_member_cannot_verify_or_accept_evidence(self):
        evidence = EvidenceItem.objects.create(
            case=self.case,
            registered_by=self.user,
            original_path="unreadable.bin",
            display_name="Read-only check",
        )
        self.user.role = "auditor"
        self.user.save()
        for endpoint, body in (
            ("verify", {}),
            ("accept-baseline", {"reason": "denied"}),
        ):
            result = self.client.post(
                f"/api/v1/evidence/{evidence.pk}/{endpoint}/", body, format="json"
            )
            self.assertEqual(result.status_code, 403)

    def test_cross_case_notes_and_bookmarks_rejected_before_save(self):
        evidence = EvidenceItem.objects.create(
            case=self.other, registered_by=self.user, original_path="unused", display_name="other"
        )
        job = ProcessingJob.objects.create(
            case=self.other, evidence=evidence, requested_by=self.user
        )
        run = ProcessingRun.objects.create(
            case=self.other, job=job, processor_name="test", processor_version="1"
        )
        artifact = Artifact.objects.create(
            case=self.other, source_evidence=evidence, processing_run=run
        )
        for endpoint, fields in (("notes", {"body": "Denied"}), ("bookmarks", {"label": "Denied"})):
            result = self.client.post(
                f"/api/v1/cases/{self.case.pk}/{endpoint}/",
                {"artifact": str(artifact.pk), **fields},
                format="json",
            )
            self.assertEqual(result.status_code, 400)
        self.assertFalse(Bookmark.objects.exists())
        self.assertFalse(InvestigatorNote.objects.exists())

    def test_outside_root_source_is_not_read(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "outside.bin"
            source.write_bytes(b"outside")
            item = EvidenceItem.objects.create(
                case=self.case,
                registered_by=self.user,
                original_path=str(source),
                display_name="outside",
                expected_hash=hashlib.sha256(b"outside").hexdigest(),
            )
            with override_settings(EVIDENCE_ROOT=str(Path(root) / "approved")):
                self.client.post(f"/api/v1/evidence/{item.pk}/verify/")
            item.refresh_from_db()
            self.assertEqual(item.verification_status, "unreadable")
            self.assertEqual(item.calculated_hash, "")

    def test_lists_are_bounded_ordered_and_validate_pagination(self):
        evidence = self.client.get(f"/api/v1/cases/{self.case.pk}/evidence/?limit=100")
        self.assertEqual(evidence.status_code, 200, evidence.data)
        self.assertIsInstance(evidence.data["results"], list)
        for index in range(105):
            Finding.objects.create(
                case=self.case, author=self.user, finding_text=f"Finding {index:03d}"
            )
        first = self.client.get(f"/api/v1/cases/{self.case.pk}/findings/?limit=100")
        second = self.client.get(f"/api/v1/cases/{self.case.pk}/findings/?limit=100&offset=100")
        self.assertEqual(first.data["count"], 106)
        self.assertEqual(len(first.data["results"]), 100)
        self.assertEqual(len(second.data["results"]), 6)
        first_ids = [row["id"] for row in first.data["results"]]
        second_ids = [row["id"] for row in second.data["results"]]
        self.assertFalse(set(first_ids) & set(second_ids))
        self.assertEqual(
            self.client.get(f"/api/v1/cases/{self.case.pk}/findings/?limit=101").status_code,
            400,
        )
