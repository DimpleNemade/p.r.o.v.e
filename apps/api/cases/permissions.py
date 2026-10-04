from rest_framework.permissions import BasePermission
from .models import CaseParticipant

CAPABILITIES = {
    "administrator": {
        "create",
        "participants",
        "evidence",
        "process",
        "finding",
        "review",
        "report",
        "export",
    },
    "supervisor": {
        "create",
        "participants",
        "evidence",
        "process",
        "finding",
        "review",
        "report",
        "export",
    },
    "investigator": {
        "create",
        "participants",
        "evidence",
        "process",
        "finding",
        "report",
        "export",
    },
    "reviewer": {"review"},
    "auditor": set(),
    "student": {"evidence", "process", "finding"},
}


def allowed(user, case=None, action="read"):
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if action == "create":
        return action in CAPABILITIES.get(user.role, set())
    membership = CaseParticipant.objects.filter(case=case, user=user).first()
    if not membership:
        return False
    if action == "read":
        return True
    if action not in CAPABILITIES.get(user.role, set()):
        return False
    if action == "participants":
        return membership.permission == "owner" and case.owner_id == user.id
    if action == "review":
        return membership.permission in {"owner", "review"}
    return membership.permission in {"owner", "edit"}


def has_case_access(user, case, write=False):
    return allowed(user, case, "finding" if write else "read")


class CaseAccessPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_case_access(
            request.user,
            obj.case if hasattr(obj, "case") else obj,
            request.method not in ("GET", "HEAD", "OPTIONS"),
        )
