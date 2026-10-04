import hashlib
import json
from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied, APIException
from audit.services import append_event
from cases.permissions import allowed
from .models import Finding, FindingRevision, ReviewDecision


class Conflict(APIException):
    status_code = 409
    default_detail = "Record changed; reload before applying this action"


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=str,
    ).encode("utf-8")


def support_snapshot(finding):
    supports = []
    for support in finding.supports.select_related("artifact", "timeline_event").order_by("id"):
        artifact = support.artifact or (
            support.timeline_event.artifact if support.timeline_event else None
        )
        if support.timeline_event and support.timeline_event.case_id != finding.case_id:
            raise ValidationError("Timeline support crosses case boundary")
        if (
            not artifact
            or artifact.case_id != finding.case_id
            or artifact.source_evidence.case_id != finding.case_id
            or artifact.processing_run.case_id != finding.case_id
            or artifact.processing_run.job.case_id != finding.case_id
            or artifact.processing_run.job.evidence_id != artifact.source_evidence_id
        ):
            raise ValidationError("Support has missing or cross-case provenance")
        evidence = artifact.source_evidence
        links = (
            artifact.provenance_links.filter(case=finding.case, source_evidence=evidence)
            if hasattr(artifact, "provenance_links")
            else None
        )
        # ProvenanceLink uses its explicit related_name on Artifact.
        if (
            links is None
            or not links.exists()
            or artifact.processing_run.status != "succeeded"
            or artifact.processing_run.job.status != "succeeded"
        ):
            raise ValidationError("Support lacks successful processing and stored provenance")
        if (
            not evidence.baseline_hash
            or evidence.verification_status not in {"verified", "baseline_accepted"}
            or artifact.source_hash_reference != evidence.baseline_hash
        ):
            raise ValidationError("Supporting evidence integrity is not currently valid")
        supports.append(
            {
                "id": str(support.pk),
                "artifact": str(artifact.pk),
                "timeline_event": str(support.timeline_event_id)
                if support.timeline_event_id
                else None,
                "evidence": str(evidence.pk),
                "input_sha256": artifact.source_hash_reference,
                "run": str(artifact.processing_run_id),
                "processor": artifact.processor_name,
                "version": artifact.processor_version,
                "content_sha256": hashlib.sha256(canonical(artifact.content)).hexdigest(),
                "provenance": [str(link.pk) for link in links.order_by("id")],
            }
        )
    if not supports:
        raise ValidationError("At least one traceable support is required")
    return supports


def transition(finding_id, actor, action, version, comments=""):
    with transaction.atomic():
        finding = Finding.objects.select_for_update().get(pk=finding_id)
        if version != finding.version:
            raise Conflict()
        author_action = action in {"submit", "withdraw", "supersede"}
        if not allowed(actor, finding.case, "finding" if author_action else "review"):
            raise PermissionDenied("Finding action denied")
        if author_action and finding.author_id != actor.pk:
            raise PermissionDenied("Only the finding author may submit or revise")
        if not author_action and finding.author_id == actor.pk:
            raise PermissionDenied(
                "An independent reviewer is required, including for administrators"
            )
        latest = finding.revisions.order_by("-number").first()
        if action == "submit":
            if finding.examiner_status != "draft":
                raise Conflict("Only drafts can be submitted")
            snapshot = {
                "text": finding.finding_text,
                "basis": finding.finding_basis,
                "supports": support_snapshot(finding),
                "case": str(finding.case_id),
                "author": str(finding.author_id),
            }
            latest = FindingRevision.objects.create(
                finding=finding,
                number=(latest.number + 1 if latest else 1),
                author=actor,
                snapshot=snapshot,
                snapshot_hash=hashlib.sha256(canonical(snapshot)).hexdigest(),
            )
            finding.examiner_status = "submitted"
            finding.review_status = "submitted"
        elif action in {"start_review", "approve", "request_changes"}:
            required = {
                "start_review": "submitted",
                "approve": "in_review",
                "request_changes": "in_review",
            }[action]
            if not latest or latest.status != required or finding.examiner_status == "draft":
                raise Conflict("Invalid review transition")
            if not comments.strip():
                raise ValidationError("Review comments are required")
            if action == "approve":
                if (
                    support_snapshot(finding) != latest.snapshot["supports"]
                    or hashlib.sha256(canonical(latest.snapshot)).hexdigest()
                    != latest.snapshot_hash
                ):
                    raise ValidationError("Revision traceability changed since submission")
            latest.status = {
                "start_review": "in_review",
                "approve": "approved",
                "request_changes": "changes_requested",
            }[action]
            latest.save(update_fields=["status"])
            ReviewDecision.objects.create(
                revision=latest, actor=actor, decision=latest.status, comments=comments
            )
            finding.review_status = latest.status
            finding.examiner_status = latest.status
        elif action in {"withdraw", "supersede"}:
            if not comments.strip() or not latest or finding.examiner_status == "draft":
                raise ValidationError("A submitted revision and recorded reason are required")
            ReviewDecision.objects.create(
                revision=latest, actor=actor, decision=action, comments=comments
            )
            # Approved snapshots and their approval decision are retained unchanged.
            finding.examiner_status = "draft" if action == "supersede" else "withdrawn"
            finding.review_status = "not_reviewed" if action == "supersede" else "withdrawn"
        else:
            raise ValidationError("Unknown finding transition")
        finding.version += 1
        finding.save()
        append_event(
            finding.case,
            actor,
            f"finding.{action}",
            "FindingRevision",
            latest.pk,
            {
                "snapshot_hash": latest.snapshot_hash,
                "version": finding.version,
                "comments": comments,
            },
        )
    return finding
