import hashlib
import tempfile
from pathlib import Path
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import Case, CaseParticipant
from evidence.models import EvidenceItem
from investigations.models import Artifact, ProvenanceLink
from audit.models import AuditEvent
from processing.models import ProcessingJob


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class InvestigationApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            "investigator",
            password="safe-password",
            role="investigator",
            display_name="Investigator",
        )
        self.other = User.objects.create_user(
            "other", password="safe-password", role="investigator"
        )
        self.case = Case.objects.create(
            reference="TEST-0001", title="Synthetic case", owner=self.user
        )
        CaseParticipant.objects.create(case=self.case, user=self.user, permission="owner")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_unauthenticated_api_is_denied(self):
        self.client.force_authenticate(None)
        response = self.client.get("/api/cases/")
        assert response.status_code == 403

    def test_login_requires_csrf_and_returns_session(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_authenticate(None)
        User = get_user_model()
        User.objects.create_user("login-user", password="safe-password")

        without_token = client.post(
            "/api/auth/login/",
            {"username": "login-user", "password": "safe-password"},
            format="json",
        )
        assert without_token.status_code == 403

        csrf_response = client.get("/api/auth/csrf/")
        token = csrf_response.data["csrfToken"]
        response = client.post(
            "/api/auth/login/",
            {"username": "login-user", "password": "safe-password"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        assert response.status_code == 200
        assert response.data["username"] == "login-user"

    def test_case_isolation_denies_non_participant(self):
        self.client.force_authenticate(self.other)
        response = self.client.get(f"/api/cases/{self.case.id}/")
        assert response.status_code == 403

    def test_evidence_hash_and_processing_create_provenance(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as handle:
            handle.write(b"synthetic evidence")
            source = Path(handle.name)
        try:
            expected = hashlib.sha256(b"synthetic evidence").hexdigest()
            response = self.client.post(
                f"/api/cases/{self.case.id}/evidence/",
                {
                    "display_name": "sample.txt",
                    "original_path": str(source),
                    "expected_hash": expected,
                },
                format="json",
            )
            assert response.status_code == 201
            evidence_id = response.data["id"]
            verified = self.client.post(f"/api/evidence/{evidence_id}/verify/")
            assert verified.status_code == 200
            assert verified.data["verification_status"] == "verified"
            job = self.client.post(
                f"/api/cases/{self.case.id}/jobs/", {"evidence": evidence_id}, format="json"
            )
            assert job.status_code == 201
            assert Artifact.objects.filter(case=self.case).exists()
            assert ProvenanceLink.objects.filter(case=self.case).exists()
            assert AuditEvent.objects.filter(case=self.case, action="processing.submitted").exists()
            assert AuditEvent.objects.filter(
                case=self.case, action="evidence.hash_verified"
            ).exists()
        finally:
            source.unlink(missing_ok=True)

    def test_hash_mismatch_is_recorded_and_processing_fails(self):
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            handle.write(b"actual")
            source = Path(handle.name)
        try:
            response = self.client.post(
                f"/api/cases/{self.case.id}/evidence/",
                {
                    "display_name": "mismatch.bin",
                    "original_path": str(source),
                    "expected_hash": "0" * 64,
                },
                format="json",
            )
            evidence_id = response.data["id"]
            verified = self.client.post(f"/api/evidence/{evidence_id}/verify/")
            assert verified.data["verification_status"] == "mismatch"
            job = self.client.post(
                f"/api/cases/{self.case.id}/jobs/", {"evidence": evidence_id}, format="json"
            )
            assert job.status_code == 201
            assert ProcessingJob.objects.get(pk=job.data["id"]).status == "failed"
        finally:
            source.unlink(missing_ok=True)
