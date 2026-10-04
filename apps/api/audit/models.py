import uuid
from django.conf import settings
from django.db import models
from cases.models import Case


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name="audit_events", null=True, blank=True
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    sequence = models.PositiveBigIntegerField(null=True, blank=True)
    schema_version = models.CharField(max_length=40, default="legacy")
    service = models.CharField(max_length=80, blank=True)
    previous_hash = models.CharField(max_length=64, blank=True)
    event_hash = models.CharField(max_length=64, blank=True)
    records_digest = models.CharField(max_length=64, blank=True)
    record_bindings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["case", "sequence"], name="audit_case_sequence")
        ]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["case", "created_at"]),
            models.Index(fields=["actor", "created_at"]),
        ]
