import uuid
from django.conf import settings
from django.db import models
from cases.models import Case
from evidence.models import EvidenceItem
from processing.models import ProcessingRun


class Artifact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="artifacts")
    source_evidence = models.ForeignKey(
        EvidenceItem, on_delete=models.PROTECT, related_name="artifacts"
    )
    source_path = models.TextField(blank=True)
    source_hash_reference = models.CharField(max_length=128, blank=True)
    processing_run = models.ForeignKey(
        ProcessingRun, on_delete=models.PROTECT, related_name="artifacts"
    )
    processor_name = models.CharField(max_length=100)
    processor_version = models.CharField(max_length=40)
    processing_timestamp = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(max_length=30, default="normalized")
    artifact_type = models.CharField(max_length=60, default="file_metadata")
    content = models.JSONField(default=dict)
    limitations = models.JSONField(default=list, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "artifact_type"]),
            models.Index(fields=["source_evidence", "created_at"]),
        ]


class TimelineEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="timeline_events")
    artifact = models.ForeignKey(
        Artifact, on_delete=models.PROTECT, null=True, blank=True, related_name="timeline_events"
    )
    observed_at = models.DateTimeField()
    event_type = models.CharField(max_length=80)
    summary = models.TextField()
    interpretation_status = models.CharField(
        max_length=30,
        default="observed",
        choices=[
            ("observed", "Observed evidence"),
            ("normalized", "Normalized interpretation"),
            ("suggestion", "Machine-generated suggestion"),
            ("approved", "Examiner-approved conclusion"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["observed_at"]
        indexes = [
            models.Index(fields=["case", "observed_at"]),
            models.Index(fields=["case", "event_type"]),
        ]


class ProvenanceLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="provenance_links")
    source_evidence = models.ForeignKey(
        EvidenceItem, on_delete=models.PROTECT, related_name="provenance_links"
    )
    artifact = models.ForeignKey(
        Artifact, on_delete=models.PROTECT, related_name="provenance_links"
    )
    relationship = models.CharField(max_length=80, default="derived_from")
    rationale = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_evidence", "artifact", "relationship"],
                name="unique_provenance_link",
            )
        ]
        indexes = [models.Index(fields=["case", "created_at"])]


class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="bookmarks")
    artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE, related_name="bookmarks")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    label = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class InvestigatorNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    artifact = models.ForeignKey(Artifact, on_delete=models.PROTECT, null=True, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Finding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="findings")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    finding_text = models.TextField()
    finding_basis = models.CharField(
        max_length=30,
        default="observed",
        choices=[("observed", "Observed evidence"), ("interpreted", "Normalized interpretation")],
    )
    examiner_status = models.CharField(
        max_length=30,
        default="draft",
        choices=[
            ("draft", "Draft"),
            ("approved", "Examiner-approved conclusion"),
            ("withdrawn", "Withdrawn"),
        ],
    )
    review_status = models.CharField(
        max_length=30,
        default="not_reviewed",
        choices=[
            ("not_reviewed", "Not reviewed"),
            ("in_review", "In review"),
            ("reviewed", "Reviewed"),
        ],
    )
    reviewer_comments = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "review_status"]),
            models.Index(fields=["case", "created_at"]),
        ]


class FindingSupport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name="supports")
    artifact = models.ForeignKey(Artifact, on_delete=models.PROTECT, null=True, blank=True)
    timeline_event = models.ForeignKey(
        TimelineEvent, on_delete=models.PROTECT, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(artifact__isnull=False) | models.Q(timeline_event__isnull=False)
                ),
                name="finding_support_has_source",
            )
        ]
