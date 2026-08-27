from rest_framework.permissions import BasePermission
from .models import CaseParticipant


def has_case_access(user, case, write=False):
    if user.is_superuser or user.role == "administrator":
        return True
    participant = CaseParticipant.objects.filter(case=case, user=user).first()
    if not participant:
        return False
    return participant.permission in (
        {"owner", "edit", "review"} if write else {"owner", "edit", "review", "read"}
    )


class CaseAccessPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_case_access(
            request.user,
            obj.case if hasattr(obj, "case") else obj,
            request.method not in ("GET", "HEAD", "OPTIONS"),
        )
