import uuid
from django.conf import settings
from django.db import models
from cases.models import Case
from evidence.models import EvidenceItem


class ProcessingJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="processing_jobs")
    evidence = models.ForeignKey(
        EvidenceItem, on_delete=models.PROTECT, related_name="processing_jobs"
    )
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=30,
        default="queued",
        choices=[
            ("queued", "Queued"),
            ("running", "Running"),
            ("succeeded", "Succeeded"),
            ("failed", "Failed"),
        ],
    )
    error_message = models.TextField(blank=True)
    fingerprint = models.CharField(max_length=64, blank=True)
    request_key = models.CharField(max_length=100, null=True, blank=True)
    parameters = models.JSONField(default=dict)
    prior_job = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)
    reason = models.TextField(blank=True)
    claim_token = models.UUIDField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    publication_status = models.CharField(max_length=30, default="pending")
    publication_attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["case", "request_key"], name="job_case_request_key")
        ]
        indexes = [
            models.Index(fields=["case", "status"]),
            models.Index(fields=["evidence", "created_at"]),
        ]


class ProcessingRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="processing_runs")
    job = models.ForeignKey(ProcessingJob, on_delete=models.PROTECT, related_name="runs")
    processor_name = models.CharField(max_length=100)
    processor_version = models.CharField(max_length=40)
    status = models.CharField(max_length=30, default="running")
    warnings = models.JSONField(default=list, blank=True)
    errors = models.JSONField(default=list, blank=True)
    attempt_token = models.UUIDField(null=True, blank=True, unique=True)
    reproducibility = models.JSONField(default=dict)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job"],
                condition=models.Q(status="succeeded", attempt_token__isnull=False),
                name="one_successful_run_per_job",
            )
        ]
        indexes = [
            models.Index(fields=["case", "status"]),
            models.Index(fields=["job", "started_at"]),
        ]
