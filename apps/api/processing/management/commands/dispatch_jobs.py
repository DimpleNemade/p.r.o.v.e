from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from processing.models import ProcessingJob
from processing.services import publish
from audit.services import append_event


class Command(BaseCommand):
    help = "Republish queued jobs; optionally recover claims older than ten minutes."

    def add_arguments(self, parser):
        parser.add_argument("--recover-stale", action="store_true")

    def handle(self, *args, **options):
        if options["recover_stale"]:
            for pk in ProcessingJob.objects.filter(
                status="running", claimed_at__lt=timezone.now() - timedelta(minutes=10)
            ).values_list("pk", flat=True):
                with transaction.atomic():
                    job = ProcessingJob.objects.select_for_update().get(pk=pk)
                    if job.status != "running" or job.claimed_at >= timezone.now() - timedelta(
                        minutes=10
                    ):
                        continue
                    job.runs.filter(status="running").update(
                        status="interrupted",
                        finished_at=timezone.now(),
                        errors=["Expired worker claim; recovery requested"],
                    )
                    job.status = "queued"
                    job.claim_token = None
                    job.save()
                    append_event(
                        job.case,
                        job.requested_by,
                        "processing.recovered",
                        "ProcessingJob",
                        job.pk,
                        {"reason": "Expired claim after ten minutes"},
                        service="dispatcher",
                    )
        count = 0
        for pk in (
            ProcessingJob.objects.filter(status="queued")
            .order_by("created_at")
            .values_list("pk", flat=True)[:100]
        ):
            count += int(publish(pk))
        self.stdout.write(f"Published {count} queued jobs")
