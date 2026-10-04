import re
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from cases.permissions import allowed
from .models import EvidenceItem, EvidenceHash, CustodyEvent
from .storage import read_source, SourceDenied


def validate_digest(algorithm, digest):
    if algorithm != "SHA-256" or (digest and not re.fullmatch(r"[a-fA-F0-9]{64}", digest)):
        raise ValidationError("Only SHA-256 with a 64-character hexadecimal digest is supported")


def observe(evidence, actor):
    if not allowed(actor, evidence.case, "evidence"):
        raise PermissionDenied("Evidence action denied")
    validate_digest(evidence.hash_algorithm, evidence.expected_hash)
    metadata, content = {}, b""
    try:
        content, digest, metadata = read_source(evidence)
        failure = False
    except (OSError, SourceDenied):
        digest, failure = "", True
    with transaction.atomic():
        current = EvidenceItem.objects.select_for_update().get(pk=evidence.pk)
        reference = current.baseline_hash or current.expected_hash.lower()
        state = "unreadable" if failure else "baseline_pending"
        if not failure and reference:
            state = (
                (
                    "baseline_accepted"
                    if current.baseline_origin == "local_acceptance"
                    else "verified"
                )
                if digest == reference
                else "mismatch"
            )
        if state == "verified" and not current.baseline_hash:
            current.baseline_hash = reference
            current.baseline_origin = "operator_reference"
            current.baseline_accepted_by = actor
            current.baseline_accepted_at = timezone.now()
            current.baseline_reason = "Successful comparison with operator reference; authenticity not independently established."
        current.calculated_hash, current.verification_status = digest, state
        current.save()
        observation = EvidenceHash.objects.create(
            evidence=current, value=digest, status=state, actor=actor, file_metadata=metadata
        )
        action = {
            "verified": "hash_verified",
            "baseline_accepted": "baseline_compared",
            "baseline_pending": "baseline_observed",
            "mismatch": "hash_mismatch",
            "unreadable": "hash_verification_failed",
        }[state]
        custody = CustodyEvent.objects.create(
            case=current.case,
            evidence=current,
            actor=actor,
            action=action,
            details={"status": state, "observation": str(observation.id)},
        )
        from audit.services import append_event

        append_event(
            current.case,
            actor,
            f"evidence.{action}",
            "EvidenceItem",
            current.id,
            {"status": state, "observation": str(observation.id), "custody": str(custody.id)},
        )
    evidence.refresh_from_db()
    return content, digest, metadata


def accept_baseline(evidence, actor, reason):
    if not allowed(actor, evidence.case, "evidence"):
        raise PermissionDenied("Evidence action denied")
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError("A baseline acceptance reason is required")
    previous = evidence.calculated_hash
    observe(evidence, actor)
    with transaction.atomic():
        current = EvidenceItem.objects.select_for_update().get(pk=evidence.pk)
        if (
            current.expected_hash
            or current.baseline_hash
            or current.verification_status != "baseline_pending"
            or not previous
            or previous != current.calculated_hash
        ):
            raise ValidationError(
                "Observe the current input before accepting an unreferenced baseline"
            )
        current.baseline_hash = current.calculated_hash
        current.baseline_origin = "local_acceptance"
        current.baseline_accepted_by = actor
        current.baseline_accepted_at = timezone.now()
        current.baseline_reason = reason.strip()
        current.verification_status = "baseline_accepted"
        current.save()
        from audit.services import append_event

        append_event(
            current.case,
            actor,
            "evidence.baseline_accepted",
            "EvidenceItem",
            current.id,
            {
                "reason": reason,
                "limitation": "Local acceptance does not verify acquisition authenticity.",
            },
        )
    evidence.refresh_from_db()
