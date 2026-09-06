import uuid
from django.conf import settings
from django.db import models
from cases.models import Case


class EvidenceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="evidence_items")
    evidence_type = models.CharField(max_length=60, default="synthetic_file")
    display_name = models.CharField(max_length=200)
    original_path = models.TextField()
    acquisition_metadata = models.JSONField(default=dict, blank=True)
    hash_algorithm = models.CharField(max_length=20, default="SHA-256")
    expected_hash = models.CharField(max_length=64, blank=True)
    calculated_hash = models.CharField(max_length=64, blank=True)
    verification_status = models.CharField(
        max_length=30,
        default="unverified",
        choices=[
            ("unverified", "Unverified"),
            ("verified", "Verified"),
            ("mismatch", "Mismatch"),
            ("unreadable", "Unreadable"),
        ],
    )
    read_only = models.BooleanField(default=True)
    is_synthetic = models.BooleanField(default=False)
    warnings = models.JSONField(default=list, blank=True)
    limitations = models.JSONField(default=list, blank=True)
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="registered_evidence"
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "verification_status"]),
            models.Index(fields=["case", "registered_at"]),
        ]


class EvidenceHash(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey(EvidenceItem, on_delete=models.CASCADE, related_name="hashes")
    algorithm = models.CharField(max_length=20, default="SHA-256")
    value = models.CharField(max_length=128)
    source = models.CharField(max_length=30, default="calculated")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["evidence", "algorithm"])]


class CustodyEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="custody_events")
    evidence = models.ForeignKey(
        EvidenceItem, on_delete=models.PROTECT, related_name="custody_events"
    )
    action = models.CharField(max_length=60)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["case", "created_at"]),
            models.Index(fields=["evidence", "created_at"]),
        ]
