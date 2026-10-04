"""Bounded deterministic ZIP format and offline verifier; no Django dependency."""

import hashlib
import io
import json
import zipfile
from pathlib import PurePosixPath

SCHEMA = "prove.handoff/1"
MAX_BYTES = 32 * 1024 * 1024
GUIDE = b"P.R.O.V.E. handoff v1\nRun: python scripts/verify_package.py package.zip\nOriginal evidence excluded. Checksums establish consistency, not author authenticity.\nSource time may be unknown. Retain the case checkpoint independently to detect tail deletion.\n"


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def build(snapshot):
    content = canonical(snapshot)
    if len(content) > MAX_BYTES - 65536:
        raise ValueError("Snapshot exceeds package limit")
    files = {"snapshot.json": content, "GUIDE.txt": GUIDE}
    manifest = {
        "schema": SCHEMA,
        "content_digest": hashlib.sha256(content).hexdigest(),
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            for name, data in files.items()
        },
    }
    files["manifest.json"] = canonical(manifest)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100600 << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, data)
    return buffer.getvalue(), manifest


def parse_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    return json.loads(
        raw,
        object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Invalid JSON number")),
    )


def verify(data):
    if len(data) > MAX_BYTES:
        raise ValueError("Archive exceeds size limit")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        if len(infos) != 3 or len({i.filename for i in infos}) != len(infos):
            raise ValueError("Unexpected or duplicate archive entries")
        for info in infos:
            name = info.filename
            if (
                PurePosixPath(name).is_absolute()
                or ".." in PurePosixPath(name).parts
                or "\\" in name
                or ":" in name
                or name not in {"manifest.json", "snapshot.json", "GUIDE.txt"}
            ):
                raise ValueError("Disallowed archive path")
            if (
                info.file_size > MAX_BYTES
                or info.flag_bits & 1
                or info.compress_type != zipfile.ZIP_STORED
            ):
                raise ValueError("Unsupported or oversized archive entry")
        if sum(i.file_size for i in infos) > MAX_BYTES:
            raise ValueError("Expanded package exceeds limit")
        manifest = parse_json(archive.read("manifest.json"))
        if (
            not isinstance(manifest, dict)
            or set(manifest) != {"schema", "content_digest", "files"}
            or manifest["schema"] != SCHEMA
            or set(manifest["files"]) != {"snapshot.json", "GUIDE.txt"}
        ):
            raise ValueError("Invalid manifest schema")
        for name, record in manifest["files"].items():
            content = archive.read(name)
            if (
                set(record) != {"sha256", "size"}
                or record["size"] != len(content)
                or record["sha256"] != hashlib.sha256(content).hexdigest()
            ):
                raise ValueError(f"Content hash mismatch: {name}")
        snapshot = parse_json(archive.read("snapshot.json"))
        if digest(snapshot) != manifest["content_digest"] or canonical(snapshot) != archive.read(
            "snapshot.json"
        ):
            raise ValueError("Snapshot content digest or canonical encoding mismatch")
    validate_snapshot(snapshot)
    return {
        "valid": True,
        "schema": SCHEMA,
        "content_digest": manifest["content_digest"],
        "case_id": snapshot["case"]["id"],
        "checkpoint": snapshot["checkpoint"],
        "limitations": [
            "Unsigned manifest: consistency, not author authentication",
            "No original evidence included",
        ],
    }


def validate_snapshot(s):
    expected = {
        "schema",
        "case",
        "evidence",
        "observations",
        "custody",
        "provenance",
        "jobs",
        "runs",
        "artifacts",
        "timeline",
        "findings",
        "revisions",
        "decisions",
        "report",
        "audit",
        "checkpoint",
        "warnings",
        "exclusions",
        "limitations",
    }
    if not isinstance(s, dict) or set(s) != expected or s["schema"] != SCHEMA:
        raise ValueError("Invalid snapshot schema")
    case_id = s["case"]["id"]
    maps = {}
    for kind in (
        "evidence",
        "observations",
        "custody",
        "provenance",
        "jobs",
        "runs",
        "artifacts",
        "timeline",
        "findings",
        "revisions",
        "decisions",
    ):
        rows = s[kind]
        if not isinstance(rows, list) or len(rows) > 10000:
            raise ValueError("Invalid or oversized record list")
        maps[kind] = {row["id"]: row for row in rows}
        if len(maps[kind]) != len(rows) or any(
            row.get("case_id", case_id) != case_id for row in rows
        ):
            raise ValueError("Duplicate record or case isolation failure")
    relations = {
        "observations": {"evidence_id": "evidence"},
        "custody": {"evidence_id": "evidence"},
        "provenance": {"source_evidence_id": "evidence", "artifact_id": "artifacts"},
        "jobs": {"evidence_id": "evidence", "prior_job_id": "jobs"},
        "runs": {"job_id": "jobs"},
        "artifacts": {"source_evidence_id": "evidence", "processing_run_id": "runs"},
        "timeline": {"artifact_id": "artifacts"},
        "revisions": {"finding_id": "findings"},
        "decisions": {"revision_id": "revisions"},
    }
    for kind, fields in relations.items():
        for row in s[kind]:
            for field, target in fields.items():
                if row.get(field) and row[field] not in maps[target]:
                    raise ValueError(f"Missing {kind}.{field} reference")
    for revision in s["revisions"]:
        if digest(revision["snapshot"]) != revision["snapshot_hash"]:
            raise ValueError("Finding revision digest mismatch")
        for support in revision["snapshot"]["supports"]:
            if (
                support["artifact"] not in maps["artifacts"]
                or support["evidence"] not in maps["evidence"]
                or support["run"] not in maps["runs"]
                or any(link not in maps["provenance"] for link in support["provenance"])
            ):
                raise ValueError("Revision support reference missing")
    previous = "0" * 64
    for index, event in enumerate(s["audit"], 1):
        payload = {
            key: value
            for key, value in event.items()
            if key not in {"event_hash", "record_bindings"}
        }
        if (
            event["case_id"] != case_id
            or event["sequence"] != index
            or event["previous_hash"] != previous
            or digest(payload) != event["event_hash"]
        ):
            raise ValueError("Invalid audit chain")
        previous = event["event_hash"]
        if event.get("record_bindings"):
            if digest(event["record_bindings"]) != event["records_digest"] or any(
                maps[kind].get(row["id"]) != row
                for kind, rows in event["record_bindings"].items()
                for row in rows
            ):
                raise ValueError("Changed or missing bound custody/provenance record")
    if s["audit"] and s["audit"][-1]["records_digest"] != digest(
        {"custody": s["custody"], "provenance": s["provenance"]}
    ):
        raise ValueError("Custody/provenance ledger binding mismatch")
    if s["checkpoint"] != {"case_id": case_id, "sequence": len(s["audit"]), "event_hash": previous}:
        raise ValueError("Audit cutoff checkpoint mismatch")
