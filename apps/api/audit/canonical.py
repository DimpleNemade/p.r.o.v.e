"""prove.canonical/1: UTF-8 JSON, sorted keys, no whitespace/NaN, no NFC rewrite."""

import hashlib
import json


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=str,
    ).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


EVENT_FIELDS = (
    "id",
    "case_id",
    "sequence",
    "schema_version",
    "actor_id",
    "service",
    "action",
    "object_type",
    "object_id",
    "metadata",
    "created_at",
    "previous_hash",
    "records_digest",
)


def event_payload(event):
    value = {field: getattr(event, field) for field in EVENT_FIELDS if field != "metadata"}
    value["metadata_digest"] = digest(event.metadata)
    return json.loads(canonical(value))
