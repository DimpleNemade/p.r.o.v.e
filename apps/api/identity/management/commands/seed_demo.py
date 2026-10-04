"""Explicit, create-once synthetic fixture. Never repair investigator records."""

import hashlib
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from audit.services import append_event
from cases.models import Case, CaseParticipant
from evidence.models import EvidenceItem, CustodyEvent
from evidence.services import observe
from investigations.models import Finding, FindingSupport
from processing.models import ProcessingJob
from processing.tasks import process_evidence_job
from reporting.models import Report


class Command(BaseCommand):
    help = "Create DEMO-PHASE3-0001 once, with explicitly synthetic case-local sources."

    def handle(self, *args, **options):
        if settings.PROFILE not in {"development", "test"}:
            raise CommandError("Synthetic seeding disabled outside development/test")
        reference = "DEMO-PHASE3-0001"
        if Case.objects.filter(reference=reference).exists():
            self.stdout.write(
                "Existing synthetic fixture preserved; no records or passwords changed."
            )
            return
        User = get_user_model()
        users = {}
        for username, role in (
            ("investigator@example.test", "investigator"),
            ("reviewer@example.test", "reviewer"),
        ):
            user, created = User.objects.get_or_create(
                username=username, defaults={"role": role, "display_name": f"Synthetic {role}"}
            )
            if created:
                user.set_password("ChangeMe-Phase3-only")
                user.save()
            elif user.role != role:
                raise CommandError("Existing account has incompatible role; no changes made")
            users[role] = user
        user = users["investigator"]
        with transaction.atomic():
            case = Case.objects.create(
                reference=reference,
                title="Synthetic training case",
                description="seed_demo:phase3:v1; synthetic fixtures only",
                owner=user,
            )
            CaseParticipant.objects.create(case=case, user=user, permission="owner")
            CaseParticipant.objects.create(case=case, user=users["reviewer"], permission="review")
            append_event(case, user, "case.created", "Case", case.pk, {"fixture": "phase3:v1"})
        root = Path(settings.EVIDENCE_ROOT) / str(case.pk)
        root.mkdir(parents=True, exist_ok=True)
        for name in (
            "synthetic-evidence.txt",
            "synthetic-browser-history.txt",
            "synthetic-chat-export.json",
        ):
            content = f"Synthetic fixture {name}; no real investigation data.\n".encode()
            with (root / name).open("xb") as handle:
                handle.write(content)
            with transaction.atomic():
                evidence = EvidenceItem.objects.create(
                    case=case,
                    display_name=name,
                    original_path=name,
                    expected_hash=hashlib.sha256(content).hexdigest(),
                    registered_by=user,
                    is_synthetic=True,
                    acquisition_metadata={"fixture": "phase3:v1"},
                )
                custody = CustodyEvent.objects.create(
                    case=case,
                    evidence=evidence,
                    actor=user,
                    action="registered",
                    details={"synthetic": True},
                )
                append_event(
                    case,
                    user,
                    "evidence.registered",
                    "EvidenceItem",
                    evidence.pk,
                    {"custody": str(custody.pk)},
                )
            observe(evidence, user)
            job = ProcessingJob.objects.create(case=case, evidence=evidence, requested_by=user)
            process_evidence_job(str(job.pk))
        artifact = case.artifacts.first()
        if artifact:
            with transaction.atomic():
                finding = Finding.objects.create(
                    case=case,
                    author=user,
                    finding_text="Synthetic metadata was observed in the registered evidence set.",
                )
                FindingSupport.objects.create(finding=finding, artifact=artifact)
                append_event(case, user, "finding.created", "Finding", finding.pk)
                report = Report.objects.create(
                    case=case,
                    created_by=user,
                    title=f"Draft report: {reference}",
                    body={
                        "draftNotice": "Development draft. Not court-ready and not forensically validated.",
                        "status": "draft",
                        "findings": [],
                    },
                )
                append_event(case, user, "report.draft_generated", "Report", report.pk)
        self.stdout.write(
            "Synthetic Phase 3 fixture created. Repeat setup preserves all existing records."
        )
