from django.db import migrations


def label(apps, schema_editor):
    # Retain every original observed_at. Label rather than invent source time.
    TimelineEvent = apps.get_model("investigations", "TimelineEvent")
    TimelineEvent.objects.filter(
        timestamp_meaning="unknown", event_type__in=["file_registered", "synthetic_metadata"]
    ).update(
        timestamp_meaning="legacy_processing_or_seed_time",
        timestamp_uncertainty="Legacy value retained; not a verified source-event timestamp",
    )


class Migration(migrations.Migration):
    dependencies = [("investigations", "0004_findingrevision_reviewdecision_and_more")]
    operations = [migrations.RunPython(label, migrations.RunPython.noop)]
