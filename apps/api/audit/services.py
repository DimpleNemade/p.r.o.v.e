from django.db import transaction
from django.db.models import F
from cases.models import Case
from .models import AuditEvent
from .canonical import digest, event_payload
from .records import bound_records


def append_event(case, actor, action, object_type="", object_id="", metadata=None, service=""):
    if case is None:
        return AuditEvent.objects.create(
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=str(object_id),
            metadata=metadata or {},
            service=service,
        )
    with transaction.atomic():
        # Atomic counter update serializes appends, including SQLite writers.
        Case.objects.filter(pk=case.pk).update(ledger_sequence=F("ledger_sequence") + 1)
        current = Case.objects.select_for_update().get(pk=case.pk)
        previous = (
            AuditEvent.objects.filter(case=case, sequence__isnull=False)
            .order_by("-sequence")
            .first()
        )
        records = bound_records(case)
        event = AuditEvent.objects.create(
            case=case,
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=str(object_id),
            metadata=metadata or {},
            service=service,
            sequence=current.ledger_sequence,
            schema_version="prove.audit/1",
            previous_hash=previous.event_hash if previous else "0" * 64,
            records_digest=digest(records),
            record_bindings=records,
        )
        event.event_hash = digest(event_payload(event))
        event.save(update_fields=["event_hash"])
        return event


def verify_case(case, checkpoint=None):
    errors = []
    previous = "0" * 64
    events = list(case.audit_events.filter(sequence__isnull=False).order_by("sequence"))
    current_records = bound_records(case)
    current_maps = {
        kind: {row["id"]: row for row in rows} for kind, rows in current_records.items()
    }
    for index, event in enumerate(events, 1):
        if (
            event.sequence != index
            or event.previous_hash != previous
            or event.event_hash != digest(event_payload(event))
        ):
            errors.append(f"Invalid audit event at sequence {index}")
        if event.record_bindings:
            if digest(event.record_bindings) != event.records_digest or any(
                current_maps[kind].get(row["id"]) != row
                for kind, rows in event.record_bindings.items()
                for row in rows
            ):
                errors.append(f"Changed or missing bound record at sequence {index}")
        if event.action == "audit.legacy_checkpoint":
            legacy = list(
                case.audit_events.filter(sequence__isnull=True)
                .order_by("created_at", "id")
                .values(
                    "id",
                    "case_id",
                    "actor_id",
                    "action",
                    "object_type",
                    "object_id",
                    "metadata",
                    "created_at",
                )
            )
            if digest(legacy) != event.metadata.get("legacy_digest"):
                errors.append("Legacy history changed after migration checkpoint")
        previous = event.event_hash
    if events and events[-1].records_digest != digest(bound_records(case)):
        errors.append("Custody or provenance records differ from ledger binding")
    if checkpoint:
        event = next(
            (event for event in events if event.sequence == checkpoint.get("sequence")), None
        )
        if (
            not event
            or event.event_hash != checkpoint.get("event_hash")
            or str(case.pk) != checkpoint.get("case_id")
        ):
            errors.append("Externally retained checkpoint mismatch or missing tail")
    return {
        "valid": not errors,
        "errors": errors,
        "checkpoint": {
            "case_id": str(case.pk),
            "sequence": events[-1].sequence if events else 0,
            "event_hash": previous,
        },
        "limitations": [
            "Local hashes do not defeat an administrator rewriting records and hashes.",
            "Tail deletion requires a separately retained trusted checkpoint.",
            "Legacy history was first bound at its migration checkpoint.",
        ],
    }
