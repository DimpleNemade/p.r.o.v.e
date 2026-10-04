import io
import json
import warnings
import zipfile
from pathlib import Path
from django.conf import settings
from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient
from cases.models import Case, CaseParticipant
from .services import create_package
from .package import build, verify


class PackageTests(TestCase):
    def setUp(self):
        call_command("seed_demo")
        self.case = Case.objects.get(reference="DEMO-PHASE3-0001")
        self.actor = self.case.owner
        self.client = APIClient()
        self.client.force_authenticate(self.actor)

    def test_actual_create_status_download_and_offline_verification(self):
        result = self.client.post(
            f"/api/v1/cases/{self.case.pk}/exports/", {"report": str(self.case.reports.first().pk)}
        )
        self.assertEqual(result.status_code, 201, result.data)
        self.assertEqual(result.data["status"], "ready")
        self.assertEqual(self.client.get(f"/api/v1/exports/{result.data['id']}/").status_code, 200)
        response = self.client.get(result.data["download_url"])
        content = b"".join(response.streaming_content)
        response.close()
        self.assertTrue(verify(content)["valid"])
        self.assertNotIn(str(settings.EVIDENCE_ROOT).encode(), content)
        self.assertNotIn(b"ChangeMe", content)
        self.assertNotIn(b"original_path", content)
        self.assertTrue(self.case.audit_events.filter(action="export.downloaded").exists())

    def test_snapshot_stability_and_audit_cutoff(self):
        package = create_package(self.case, self.actor)
        archive1, manifest1 = build(package.snapshot)
        archive2, manifest2 = build(package.snapshot)
        self.assertEqual(archive1, archive2)
        self.assertEqual(manifest1, manifest2)
        self.assertFalse(any(e["object_id"] == str(package.pk) for e in package.snapshot["audit"]))
        self.assertLess(package.snapshot["checkpoint"]["sequence"], self.case.audit_events.count())
        package2 = create_package(self.case, self.actor)
        self.assertNotEqual(package.content_digest, package2.content_digest)

    def test_current_permission_revocation_blocks_download(self):
        package = create_package(self.case, self.actor)
        CaseParticipant.objects.filter(case=self.case, user=self.actor).update(permission="read")
        self.assertEqual(
            self.client.get(f"/api/v1/exports/{package.pk}/download/").status_code, 403
        )
        self.assertEqual(self.client.get(f"/api/v1/exports/{package.pk}/").status_code, 403)

    def test_altered_missing_substituted_records_and_bad_zip_rejected(self):
        package = create_package(self.case, self.actor)
        archive, _ = build(package.snapshot)
        with zipfile.ZipFile(io.BytesIO(archive)) as original:
            files = {name: original.read(name) for name in original.namelist()}
        for mutation in ("altered", "missing", "traversal", "duplicate"):
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as target:
                for name, content in files.items():
                    if mutation == "missing" and name == "snapshot.json":
                        continue
                    target.writestr(
                        name,
                        content + b" "
                        if mutation == "altered" and name == "snapshot.json"
                        else content,
                    )
                if mutation == "traversal":
                    target.writestr("../secret", b"bad")
                if mutation == "duplicate":
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        target.writestr("snapshot.json", files["snapshot.json"])
            with self.assertRaises(ValueError):
                verify(output.getvalue())
        broken = json.loads(json.dumps(package.snapshot))
        broken["artifacts"][0]["source_evidence_id"] = "substituted-record"
        altered, _ = build(broken)
        with self.assertRaises(ValueError):
            verify(altered)
