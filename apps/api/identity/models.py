import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=160, blank=True)
    role = models.CharField(
        max_length=40,
        default="investigator",
        choices=[
            ("administrator", "Administrator"),
            ("supervisor", "Case Supervisor"),
            ("investigator", "Investigator"),
            ("reviewer", "Reviewer"),
            ("auditor", "Read-only Auditor"),
            ("student", "Student/Trainee"),
        ],
    )

    class Meta:
        indexes = [models.Index(fields=["role"])]

    def __str__(self):
        return self.display_name or self.get_username()
