from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cases.models import Case, CaseParticipant
from evidence.models import EvidenceItem


class Command(BaseCommand):
    help = "Create a safe synthetic demo user, case, and evidence reference."

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(
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
        user.save()
        case, _ = Case.objects.get_or_create(
            reference="DEMO-0001",
            defaults={
                "title": "Synthetic training case",
                "description": "Safe synthetic evidence only.",
                "owner": user,
            },
        )
        CaseParticipant.objects.get_or_create(
            case=case, user=user, defaults={"permission": "owner"}
        )
        sample = Path(__file__).resolve().parents[5] / "demo" / "synthetic-evidence.txt"
        sample.parent.mkdir(parents=True, exist_ok=True)
        if not sample.exists():
            sample.write_text(
                "Synthetic evidence fixture; contains no real case data.\n", encoding="utf-8"
            )
        EvidenceItem.objects.get_or_create(
            case=case,
            display_name="synthetic-evidence.txt",
            defaults={
                "evidence_type": "synthetic_file",
                "original_path": str(sample),
                "registered_by": user,
                "acquisition_metadata": {"source": "seed_demo", "synthetic": True},
            },
        )
        self.stdout.write(
            self.style.SUCCESS("Demo data ready: admin@example.test / ChangeMe-V0.1-only")
        )
