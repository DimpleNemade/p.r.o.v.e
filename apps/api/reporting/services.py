import hashlib
import json
from pathlib import Path, PureWindowsPath
from django.conf import settings
from django.db import transaction, connection
from rest_framework.exceptions import PermissionDenied, ValidationError
from audit.canonical import canonical, event_payload
from audit.records import bound_records
from audit.services import append_event, verify_case
from cases.permissions import allowed
from .models import ExportPackage
from .package import SCHEMA, build, verify


def rows(queryset, fields):
    if queryset.count() > 10000:
        raise ValidationError("Package record limit exceeded")
    return json.loads(canonical(list(queryset.order_by("id").values(*fields.split()))))


def locator(value):
    return (
        "legacy-source-redacted"
        if PureWindowsPath(value).drive or value.startswith("/") or "\\" in value
        else value
    )


def capture(case, report):
    verification = verify_case(case)
    if not verification["valid"]:
        raise ValidationError("Ledger verification failed; export refused")
    records = bound_records(case)
    evidence = rows(
        case.evidence_items,
        "id case_id display_name evidence_type hash_algorithm expected_hash baseline_hash baseline_origin baseline_accepted_by_id baseline_accepted_at baseline_reason calculated_hash verification_status is_synthetic registered_by_id registered_at",
    )
    for row in evidence:
        item = case.evidence_items.get(pk=row["id"])
        row["source_locator"] = locator(item.original_path)
    from evidence.models import EvidenceHash
    from investigations.models import FindingRevision, ReviewDecision

    snapshot = {
        "schema": SCHEMA,
        "case": {"id": str(case.pk), "reference": case.reference, "title": case.title},
        "evidence": evidence,
        "observations": rows(
            EvidenceHash.objects.filter(evidence__case=case),
            "id evidence_id algorithm value source status actor_id created_at",
        ),
        **records,
        "jobs": rows(
            case.processing_jobs,
            "id case_id evidence_id requested_by_id status fingerprint parameters prior_job_id reason created_at",
        ),
        "runs": rows(
            case.processing_runs,
            "id case_id job_id processor_name processor_version status warnings errors reproducibility started_at finished_at",
        ),
        "artifacts": rows(
            case.artifacts,
            "id case_id source_evidence_id source_hash_reference processing_run_id processor_name processor_version processing_timestamp processing_status artifact_type content limitations warnings",
        ),
        "timeline": rows(
            case.timeline_events,
            "id case_id artifact_id observed_at timestamp_original timestamp_format timestamp_zone timestamp_meaning timestamp_precision timestamp_uncertainty event_type summary interpretation_status created_at",
        ),
        "findings": rows(
            case.findings,
            "id case_id author_id finding_text finding_basis examiner_status review_status version created_at updated_at",
        ),
        "revisions": rows(
            FindingRevision.objects.filter(finding__case=case),
            "id finding_id number author_id snapshot snapshot_hash status created_at",
        ),
        "decisions": rows(
            ReviewDecision.objects.filter(revision__finding__case=case),
            "id revision_id actor_id decision comments created_at",
        ),
        "report": None,
        "audit": [
            {
                **event_payload(event),
                "event_hash": event.event_hash,
                "record_bindings": event.record_bindings,
            }
            for event in case.audit_events.filter(sequence__isnull=False).order_by("sequence")
        ],
        "checkpoint": verification["checkpoint"],
        "warnings": [
            "Source event times may be unknown",
            "Legacy records may lack Phase 3 reproducibility or review snapshots",
        ],
        "exclusions": [
            "Original evidence",
            "Private storage paths",
            "Arbitrary acquisition and audit metadata",
            "Account credentials",
            "Unrelated cases",
        ],
        "limitations": verification["limitations"]
        + [
            "Unsigned checksums establish consistency, not author authenticity.",
            "read_only is application intent, not an operating-system write blocker.",
            "Basic metadata processor is not a validated forensic parser.",
            "record_digest binds complete custody/provenance rows; private fields are not disclosed for offline reconstruction.",
        ],
    }
    for row in snapshot["runs"]:
        # Explicit allowlist for reproducibility; excludes file identity and private paths.
        row["reproducibility"] = {
            k: v
            for k, v in row["reproducibility"].items()
            if k
            in {
                "input_sha256",
                "fingerprint",
                "parameters",
                "schema",
                "python",
                "django",
                "output_sha256",
                "execution",
            }
        }
        row["errors"] = (
            ["Processing failed; consult authorized case history"] if row["errors"] else []
        )
    for row in snapshot["artifacts"]:
        row["content"] = {
            k: v for k, v in row["content"].items() if k in {"sizeBytes", "sha256", "synthetic"}
        }
        row["source_locator"] = locator(case.artifacts.get(pk=row["id"]).source_path)
    if report:
        if report.case_id != case.pk:
            raise ValidationError("Report must belong to case")
        snapshot["report"] = {
            "id": str(report.pk),
            "case_id": str(case.pk),
            "title": report.title,
            "status": report.status,
            "created_at": str(report.created_at),
            "created_by_id": str(report.created_by_id),
            "body": {
                key: report.body[key]
                for key in ("draftNotice", "status", "approvedRevisions")
                if key in report.body
            },
        }
    return snapshot


def create_package(case, actor, report=None):
    if not allowed(actor, case, "export"):
        raise PermissionDenied("Export denied")
    # PostgreSQL only accepts SET TRANSACTION ISOLATION LEVEL as the first
    # statement of a fresh transaction, so upgrade to REPEATABLE READ only when
    # this atomic block is the outermost one (not a savepoint inside an existing
    # transaction, e.g. a test's wrapper). Otherwise the capture still runs in a
    # single transaction at the connection's default isolation level.
    upgrade_isolation = connection.vendor == "postgresql" and not connection.in_atomic_block
    with transaction.atomic():
        if upgrade_isolation:
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        snapshot = capture(case, report)
        archive, manifest = build(snapshot)
        verify(archive)
        package = ExportPackage.objects.create(
            case=case,
            requested_by=actor,
            report=report,
            snapshot=snapshot,
            content_digest=manifest["content_digest"],
            manifest_hash=hashlib.sha256(canonical(manifest)).hexdigest(),
            status="captured",
        )
        # Export identity and event are outside the captured audit cutoff.
        append_event(
            case,
            actor,
            "export.captured",
            "ExportPackage",
            package.pk,
            {
                "content_digest": package.content_digest,
                "cutoff": snapshot["checkpoint"]["sequence"],
            },
        )
    try:
        root = Path(settings.OUTPUT_ROOT) / "exports"
        root.mkdir(parents=True, exist_ok=True)
        name = f"{package.pk}.zip"
        with (root / name).open("xb") as output:
            output.write(archive)
        with transaction.atomic():
            package.storage_name = name
            package.status = "ready"
            package.save()
            append_event(
                case,
                actor,
                "export.ready",
                "ExportPackage",
                package.pk,
                {"content_digest": package.content_digest},
            )
    except Exception:
        package.status = "failed"
        package.error = "Private package write failed"
        package.save()
    return package
