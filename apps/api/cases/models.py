import uuid
from django.conf import settings
from django.db import models


class Case(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=80, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        default="open",
        choices=[("open", "Open"), ("review", "In review"), ("closed", "Closed")],
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_cases"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["owner", "status"])]


class CaseParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="case_participation"
    )
    permission = models.CharField(
        max_length=30,
        choices=[("owner", "Owner"), ("edit", "Edit"), ("review", "Review"), ("read", "Read")],
        default="read",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["case", "user"], name="unique_case_participant")
        ]
        indexes = [
            models.Index(fields=["case", "permission"]),
            models.Index(fields=["user", "case"]),
        ]
