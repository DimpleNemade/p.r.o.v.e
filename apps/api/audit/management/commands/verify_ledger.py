import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from cases.models import Case
from audit.services import verify_case


class Command(BaseCommand):
    help = "Read-only case ledger verification, optionally against retained checkpoint JSON"

    def add_arguments(self, parser):
        parser.add_argument("case_id")
        parser.add_argument("--checkpoint")

    def handle(self, *args, **options):
        checkpoint = (
            json.loads(Path(options["checkpoint"]).read_text()) if options["checkpoint"] else None
        )
        result = verify_case(Case.objects.get(pk=options["case_id"]), checkpoint)
        self.stdout.write(json.dumps(result, indent=2))
        if not result["valid"]:
            raise CommandError("Ledger verification failed; no history was rewritten")
