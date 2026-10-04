from django.db import migrations
from audit.canonical import canonical, digest, event_payload
from audit.records import bound_records


def checkpoint(apps, schema_editor):
    Case = apps.get_model("cases", "Case")
    Event = apps.get_model("audit", "AuditEvent")
    for case in Case.objects.all().iterator():
        legacy = list(
            Event.objects.filter(case=case, sequence__isnull=True)
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
        event = Event.objects.create(
            case=case,
            sequence=1,
            schema_version="prove.audit/1",
            action="audit.legacy_checkpoint",
            service="phase3-migration",
            previous_hash="0" * 64,
            records_digest=digest(bound_records(case)),
            metadata={
                "legacy_count": len(legacy),
                "legacy_digest": digest(legacy),
                "limitation": "First binding at migration time, not independently trusted historical custody.",
            },
        )
        event.event_hash = digest(event_payload(event))
        event.save(update_fields=["event_hash"])
        case.ledger_sequence = 1
        case.save(update_fields=["ledger_sequence"])


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0003_auditevent_event_hash_auditevent_previous_hash_and_more"),
        ("cases", "0003_case_ledger_sequence"),
    ]
    operations = [migrations.RunPython(checkpoint, migrations.RunPython.noop)]
