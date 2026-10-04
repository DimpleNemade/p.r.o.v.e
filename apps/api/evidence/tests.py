import hashlib
from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from cases.models import Case, CaseParticipant
from .models import EvidenceItem
from .services import observe, accept_baseline
from .storage import SourceDenied, source_path, opened_source


class IntegrityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("examiner")
        self.case = Case.objects.create(reference="INTEGRITY", title="Test", owner=self.user)
        CaseParticipant.objects.create(case=self.case, user=self.user, permission="owner")
        self.root = Path(settings.EVIDENCE_ROOT) / str(self.case.pk)
        self.root.mkdir(parents=True)
        self.path = self.root / "test.bin"
        self.path.write_bytes(b"known answer")
        self.evidence = EvidenceItem.objects.create(
            case=self.case, registered_by=self.user, display_name="test", original_path="test.bin"
        )

    def test_blank_reference_requires_explicit_acceptance_and_preserves_changed_observation(self):
        observe(self.evidence, self.user)
        self.assertEqual(self.evidence.verification_status, "baseline_pending")
        self.assertEqual(self.evidence.baseline_hash, "")
        accept_baseline(self.evidence, self.user, "Training input, no acquisition reference exists")
        accepted = self.evidence.baseline_hash
        self.assertEqual(self.evidence.baseline_origin, "local_acceptance")
        self.assertEqual(self.evidence.baseline_accepted_by, self.user)
        self.path.write_bytes(b"changed input")
        observe(self.evidence, self.user)
        self.assertEqual(self.evidence.verification_status, "mismatch")
        self.assertEqual(self.evidence.baseline_hash, accepted)
        self.assertNotEqual(self.evidence.calculated_hash, accepted)
        self.assertTrue(self.evidence.hashes.filter(value=accepted).exists())
        self.assertTrue(self.evidence.hashes.filter(status="mismatch").exists())

    def test_reference_comparison_and_algorithm_validation(self):
        self.evidence.expected_hash = hashlib.sha256(b"known answer").hexdigest()
        self.evidence.save()
        observe(self.evidence, self.user)
        self.assertEqual(self.evidence.verification_status, "verified")
        self.assertEqual(self.evidence.baseline_origin, "operator_reference")
        client = APIClient()
        client.force_authenticate(self.user)
        for algorithm, digest in (("MD5", "a" * 32), ("SHA-256", "z" * 64), ("SHA-256", "short")):
            response = client.post(
                f"/api/v1/cases/{self.case.pk}/evidence/",
                {
                    "display_name": "bad",
                    "original_path": "test.bin",
                    "hash_algorithm": algorithm,
                    "expected_hash": digest,
                },
            )
            self.assertEqual(response.status_code, 400)

    def test_reject_alternate_path_forms_and_other_case(self):
        for locator in (
            "../test.bin",
            "/etc/passwd",
            "C:/Windows/system.ini",
            "C:relative",
            "\\\\server\\share",
            "\\\\?\\C:\\file",
            "a//b",
            "CON",
            "a/../test.bin",
            "test.bin:stream",
            "test.bin.",
        ):
            with self.subTest(locator=locator), self.assertRaises((SourceDenied, OSError)):
                source_path(self.case.pk, locator)
        with self.assertRaises(OSError):
            source_path("other-case", "test.bin")

    def test_reparse_components_are_rejected(self):
        real = Path.lstat

        def marked(path):
            value = real(path)
            if path == self.path:
                from types import SimpleNamespace

                return SimpleNamespace(st_mode=value.st_mode, st_file_attributes=0x400)
            return value

        with patch.object(Path, "lstat", marked), self.assertRaises(SourceDenied):
            source_path(self.case.pk, "test.bin")

    def test_detect_modification_during_open_and_size_limit(self):
        with self.assertRaises(SourceDenied):
            with opened_source(self.evidence):
                self.path.write_bytes(b"changed and longer")
        with override_settings(MAX_EVIDENCE_BYTES=1):
            observe(self.evidence, self.user)
        self.assertEqual(self.evidence.verification_status, "unreadable")

    def test_acceptance_cannot_overwrite_baseline_or_accept_stale_input(self):
        from rest_framework.exceptions import ValidationError

        observe(self.evidence, self.user)
        self.path.write_bytes(b"new")
        with self.assertRaises(ValidationError):
            accept_baseline(self.evidence, self.user, "stale acceptance")
        accept_baseline(self.evidence, self.user, "current observed input")
        with self.assertRaises(ValidationError):
            accept_baseline(self.evidence, self.user, "overwrite")
