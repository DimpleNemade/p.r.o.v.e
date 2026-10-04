"""Allowlisted custody/provenance projections, with digests of complete DB rows."""

import json
from .canonical import canonical, digest


def record_projection(record, fields):
    raw = {field.attname: getattr(record, field.attname) for field in record._meta.fields}
    safe = {field: getattr(record, field) for field in fields}
    safe["record_digest"] = digest(raw)
    return json.loads(canonical(safe))


def bound_records(case):
    custody = [
        record_projection(row, ("id", "case_id", "evidence_id", "actor_id", "action", "created_at"))
        for row in case.custody_events.order_by("id")
    ]
    provenance = [
        record_projection(
            row,
            ("id", "case_id", "source_evidence_id", "artifact_id", "relationship", "created_at"),
        )
        for row in case.provenance_links.order_by("id")
    ]
    return {"custody": custody, "provenance": provenance}
