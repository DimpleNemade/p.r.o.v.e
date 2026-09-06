import hashlib
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from audit.models import AuditEvent
from cases.models import Case, CaseParticipant
from evidence.models import CustodyEvent, EvidenceHash, EvidenceItem
from investigations.models import Artifact, Finding, FindingSupport, ProvenanceLink, TimelineEvent
from processing.models import ProcessingJob, ProcessingRun
from reporting.models import Report


class Command(BaseCommand):
    help = "Create a safe, complete synthetic demo investigation."

    def handle(self, *args, **options):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username="admin@example.test",
            defaults={
                "email": "admin@example.test",
                "display_name": "Demo Administrator",
                "role": "administrator",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.set_password("ChangeMe-V0.1-only")
        user.display_name = "Demo Administrator"
        user.role = "administrator"
        user.is_staff = True
        user.is_superuser = True
        user.save()

        case, _ = Case.objects.get_or_create(
            reference="DEMO-0001",
            defaults={
                "title": "Synthetic training case",
                "description": "Synthetic data only; no real personal or forensic evidence.",
                "owner": user,
            },
        )
        CaseParticipant.objects.get_or_create(
            case=case, user=user, defaults={"permission": "owner"}
        )
        self._audit(case, user, "case.created", "Case", case.id)

        demo_root = Path(__file__).resolve().parents[5] / "demo"
        fixtures = {
            "synthetic-evidence.txt": "Synthetic evidence fixture; contains no real case data.\n",
            "synthetic-browser-history.txt": "Synthetic browser history; example.test only.\n",
            "synthetic-chat-export.json": '{"synthetic": true, "message": "Training fixture only"}\n',
        }
        evidence_items = []
        artifacts = []
        for index, (name, contents) in enumerate(fixtures.items(), start=1):
            path = demo_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(contents, encoding="utf-8")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            evidence, _ = EvidenceItem.objects.update_or_create(
                case=case,
                display_name=name,
                defaults={
                    "evidence_type": "synthetic_file",
                    "original_path": str(path),
                    "acquisition_metadata": {"source": "seed_demo", "synthetic": True},
                    "hash_algorithm": "SHA-256",
                    "expected_hash": digest,
                    "calculated_hash": digest,
                    "verification_status": "verified",
                    "read_only": True,
                    "is_synthetic": True,
                    "warnings": [],
                    "limitations": ["Synthetic fixture; basic metadata processor only."],
                    "registered_by": user,
                },
            )
            evidence_items.append(evidence)
            if not EvidenceHash.objects.filter(
                evidence=evidence, algorithm="SHA-256", value=digest
            ).exists():
                EvidenceHash.objects.create(
                    evidence=evidence,
                    algorithm="SHA-256",
                    value=digest,
                    source="seed_demo",
                )
            if not CustodyEvent.objects.filter(
                case=case, evidence=evidence, action="registered"
            ).exists():
                CustodyEvent.objects.create(
                    case=case,
                    evidence=evidence,
                    action="registered",
                    actor=user,
                    details={"synthetic": True},
                )
            if not CustodyEvent.objects.filter(
                case=case, evidence=evidence, action="hash_verified"
            ).exists():
                CustodyEvent.objects.create(
                    case=case,
                    evidence=evidence,
                    action="hash_verified",
                    actor=user,
                    details={"status": "verified", "synthetic": True},
                )
            self._audit(
                case, user, "evidence.registered", "EvidenceItem", evidence.id, {"synthetic": True}
            )
            self._audit(
                case,
                user,
                "evidence.hash_verified",
                "EvidenceItem",
                evidence.id,
                {"status": "verified"},
            )

            job = ProcessingJob.objects.filter(case=case, evidence=evidence).first()
            if not job:
                job = ProcessingJob.objects.create(
                    case=case, evidence=evidence, requested_by=user, status="succeeded"
                )
            else:
                job.status = "succeeded"
                job.error_message = ""
                job.save(update_fields=["status", "error_message", "updated_at"])
            run, _ = ProcessingRun.objects.get_or_create(
                job=job,
                defaults={
                    "case": case,
                    "processor_name": "basic-metadata",
                    "processor_version": "0.1.0",
                    "status": "succeeded",
                    "warnings": ["Basic metadata only."],
                    "finished_at": timezone.now(),
                },
            )
            artifact = (
                Artifact.objects.filter(
                    source_evidence=evidence,
                    source_hash_reference=digest,
                    artifact_type="file_metadata",
                )
                .order_by("created_at")
                .first()
            )
            if artifact is None:
                artifact = Artifact.objects.create(
                    case=case,
                    source_evidence=evidence,
                    source_path=str(path),
                    source_hash_reference=digest,
                    processing_run=run,
                    processor_name="basic-metadata",
                    processor_version="0.1.0",
                    processing_status="normalized",
                    artifact_type="file_metadata",
                    content={"name": name, "sizeBytes": path.stat().st_size, "synthetic": True},
                    limitations=["Basic metadata only; no complete forensic parser was used."],
                    warnings=[],
                )
            artifacts.append(artifact)
            TimelineEvent.objects.get_or_create(
                case=case,
                artifact=artifact,
                defaults={
                    "observed_at": timezone.now() - timedelta(hours=3 - index),
                    "event_type": "synthetic_metadata",
                    "summary": f"Observed metadata for synthetic fixture {name}.",
                    "interpretation_status": "observed",
                },
            )
            ProvenanceLink.objects.get_or_create(
                case=case,
                source_evidence=evidence,
                artifact=artifact,
                relationship="derived_from",
                defaults={
                    "rationale": "Synthetic seeded artifact derived after SHA-256 verification."
                },
            )
            self._audit(case, user, "processing.submitted", "ProcessingJob", job.id)
            self._audit(
                case,
                user,
                "processing.completed",
                "ProcessingJob",
                job.id,
                {"artifact_id": str(artifact.id)},
            )

        finding, _ = Finding.objects.get_or_create(
            case=case,
            finding_text="Synthetic metadata was observed in the registered evidence set.",
            defaults={"author": user, "finding_basis": "observed", "examiner_status": "draft"},
        )
        support, _ = FindingSupport.objects.get_or_create(finding=finding, artifact=artifacts[0])
        self._audit(
            case,
            user,
            "finding.created",
            "Finding",
            finding.id,
            {"finding_basis": finding.finding_basis},
        )
        self._audit(
            case, user, "finding.support_attached", "FindingSupport", support.id, {"artifact": True}
        )
        report_body = {
            "draftNotice": "Development draft. Not court-ready and not forensically validated.",
            "syntheticDataWarning": "Synthetic-data warning: this case contains seeded fixtures.",
            "case": {"reference": case.reference, "title": case.title},
            "evidenceRegister": [
                {"id": str(item.id), "name": item.display_name, "status": item.verification_status}
                for item in evidence_items
            ],
            "findings": [
                {"id": str(finding.id), "text": finding.finding_text, "supports": [str(support.id)]}
            ],
            "provenanceReferences": [str(artifact.id) for artifact in artifacts],
            "limitations": ["Basic metadata only; no complete forensic parser was used."],
            "status": "draft",
        }
        report, _ = Report.objects.update_or_create(
            case=case,
            title="Draft report: DEMO-0001",
            defaults={"body": report_body, "status": "draft", "created_by": user},
        )
        self._audit(case, user, "report.draft_generated", "Report", report.id, {"status": "draft"})
        self.stdout.write(
            self.style.SUCCESS(
                "Synthetic demo ready: 3 evidence items, 3 artifacts, 3 timeline events, finding, report, and audit history."
            )
        )

    @staticmethod
    def _audit(case, actor, action, object_type, object_id, metadata=None):
        if not AuditEvent.objects.filter(
            case=case, action=action, object_id=str(object_id)
        ).exists():
            AuditEvent.objects.create(
                case=case,
                actor=actor,
                action=action,
                object_type=object_type,
                object_id=str(object_id),
                metadata=metadata or {},
            )
