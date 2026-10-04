from rest_framework import serializers

from audit.models import AuditEvent
from .models import Case, CaseParticipant
from evidence.models import CustodyEvent, EvidenceHash, EvidenceItem
from investigations.models import (
    Artifact,
    Finding,
    FindingSupport,
    InvestigatorNote,
    Bookmark,
    ProvenanceLink,
    TimelineEvent,
)
from processing.models import ProcessingJob, ProcessingRun
from reporting.models import ExportPackage, Report


class ScopedSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        case = attrs.get("case") or getattr(self.instance, "case", None)
        finding = attrs.get("finding")
        if finding:
            case = finding.case
        for field in (
            "artifact",
            "timeline_event",
            "source_evidence",
            "processing_run",
            "evidence",
            "report",
        ):
            target = attrs.get(field)
            if target and (not case or target.case_id != case.pk):
                raise serializers.ValidationError({field: "Reference must belong to this case."})
            if (
                field == "artifact"
                and target
                and (
                    target.source_evidence.case_id != case.pk
                    or target.processing_run.case_id != case.pk
                )
            ):
                raise serializers.ValidationError(
                    {field: "Artifact provenance crosses case boundary."}
                )
        return attrs


class CaseSerializer(serializers.ModelSerializer):
    evidence_count = serializers.IntegerField(source="evidence_items.count", read_only=True)
    finding_count = serializers.IntegerField(source="findings.count", read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "reference",
            "title",
            "description",
            "status",
            "owner",
            "created_at",
            "updated_at",
            "evidence_count",
            "finding_count",
        ]
        read_only_fields = [
            "id",
            "owner",
            "created_at",
            "updated_at",
            "evidence_count",
            "finding_count",
        ]


class ParticipantSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        if attrs.get("permission") == "owner":
            raise serializers.ValidationError(
                "Ownership transfer is not available through participant creation."
            )
        from .permissions import CAPABILITIES

        role = attrs["user"].role
        permission = attrs.get("permission", "read")
        if permission == "edit" and "finding" not in CAPABILITIES.get(role, set()):
            raise serializers.ValidationError("Account cannot hold edit membership.")
        if permission == "review" and "review" not in CAPABILITIES.get(role, set()):
            raise serializers.ValidationError("Account cannot hold review membership.")
        return attrs

    class Meta:
        model = CaseParticipant
        fields = ["id", "case", "user", "permission", "created_at"]
        read_only_fields = ["id", "created_at"]


class CustodySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.display_name", read_only=True)

    class Meta:
        model = CustodyEvent
        fields = [
            "id",
            "case",
            "evidence",
            "action",
            "actor",
            "actor_name",
            "details",
            "created_at",
        ]
        read_only_fields = ["id", "actor", "created_at"]


class EvidenceHashSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceHash
        fields = [
            "id",
            "algorithm",
            "value",
            "source",
            "status",
            "actor",
            "file_metadata",
            "created_at",
        ]
        read_only_fields = [f.name for f in EvidenceHash._meta.fields]


class EvidenceSerializer(serializers.ModelSerializer):
    original_path = serializers.CharField(write_only=True)
    source_locator = serializers.SerializerMethodField()

    def get_source_locator(self, obj) -> str:
        from pathlib import PureWindowsPath

        value = obj.original_path
        return (
            "legacy-source-relocation-required"
            if PureWindowsPath(value).drive or value.startswith("/")
            else value
        )

    def validate(self, attrs):
        from evidence.services import validate_digest
        from evidence.storage import source_path, SourceDenied

        validate_digest(attrs.get("hash_algorithm", "SHA-256"), attrs.get("expected_hash", ""))
        try:
            source_path(attrs["case"].pk, attrs["original_path"])
        except (OSError, SourceDenied):
            raise serializers.ValidationError(
                {
                    "original_path": "Source must be a readable case-relative locator under approved storage."
                }
            )
        attrs["expected_hash"] = attrs.get("expected_hash", "").lower()
        attrs["read_only"] = True
        return attrs

    processing_status = serializers.SerializerMethodField()
    registered_by_name = serializers.CharField(source="registered_by.display_name", read_only=True)
    synthetic_label = serializers.SerializerMethodField()

    def get_processing_status(self, obj) -> str:
        latest = obj.processing_jobs.order_by("-created_at").first()
        return latest.status if latest else "not_started"

    def get_synthetic_label(self, obj) -> str:
        return "Synthetic data" if obj.is_synthetic else "Operator-registered evidence"

    class Meta:
        model = EvidenceItem
        fields = [
            "id",
            "case",
            "evidence_type",
            "display_name",
            "original_path",
            "source_locator",
            "baseline_hash",
            "baseline_origin",
            "baseline_accepted_by",
            "baseline_accepted_at",
            "baseline_reason",
            "acquisition_metadata",
            "hash_algorithm",
            "expected_hash",
            "calculated_hash",
            "verification_status",
            "read_only",
            "is_synthetic",
            "synthetic_label",
            "warnings",
            "limitations",
            "registered_by",
            "registered_by_name",
            "registered_at",
            "updated_at",
            "processing_status",
        ]
        read_only_fields = [
            "id",
            "registered_by",
            "registered_by_name",
            "registered_at",
            "updated_at",
            "calculated_hash",
            "verification_status",
            "processing_status",
            "synthetic_label",
            "baseline_hash",
            "baseline_origin",
            "baseline_accepted_by",
            "baseline_accepted_at",
            "baseline_reason",
        ]


class EvidenceDetailSerializer(EvidenceSerializer):
    custody_events = CustodySerializer(many=True, read_only=True)
    hashes = EvidenceHashSerializer(many=True, read_only=True)

    class Meta(EvidenceSerializer.Meta):
        fields = EvidenceSerializer.Meta.fields + ["custody_events", "hashes"]


class ProcessingRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingRun
        fields = [
            "id",
            "job",
            "processor_name",
            "processor_version",
            "status",
            "warnings",
            "errors",
            "reproducibility",
            "started_at",
            "finished_at",
        ]
        read_only_fields = [f.name for f in ProcessingRun._meta.fields]


class JobSerializer(ScopedSerializer):
    runs = ProcessingRunSerializer(many=True, read_only=True)

    class Meta:
        model = ProcessingJob
        fields = [
            "id",
            "case",
            "evidence",
            "requested_by",
            "status",
            "error_message",
            "created_at",
            "updated_at",
            "runs",
            "fingerprint",
            "prior_job",
            "reason",
            "publication_status",
            "parameters",
        ]
        read_only_fields = [
            "id",
            "requested_by",
            "status",
            "error_message",
            "created_at",
            "updated_at",
            "runs",
            "fingerprint",
            "prior_job",
            "reason",
            "publication_status",
            "parameters",
        ]


class ArtifactSerializer(serializers.ModelSerializer):
    source_path = serializers.SerializerMethodField()

    def get_source_path(self, obj) -> str:
        from pathlib import PureWindowsPath

        return (
            "legacy-source-relocation-required"
            if PureWindowsPath(obj.source_path).drive
            or obj.source_path.startswith("/")
            or "\\" in obj.source_path
            else obj.source_path
        )

    class Meta:
        model = Artifact
        fields = [
            "id",
            "case",
            "source_evidence",
            "source_path",
            "source_hash_reference",
            "processing_run",
            "processor_name",
            "processor_version",
            "processing_timestamp",
            "processing_status",
            "artifact_type",
            "content",
            "limitations",
            "warnings",
            "created_at",
        ]
        read_only_fields = [f.name for f in Artifact._meta.fields]


class ArtifactDetailSerializer(ArtifactSerializer):
    source_evidence = EvidenceSerializer(read_only=True)
    processing_run = ProcessingRunSerializer(read_only=True)
    timeline_events = serializers.SerializerMethodField()
    related_findings = serializers.SerializerMethodField()

    def get_timeline_events(self, obj) -> list:
        return TimelineSerializer(obj.timeline_events.filter(case=obj.case), many=True).data

    def get_related_findings(self, obj) -> list:
        return FindingSerializer(
            Finding.objects.filter(supports__artifact=obj, case=obj.case).distinct(), many=True
        ).data

    class Meta(ArtifactSerializer.Meta):
        fields = ArtifactSerializer.Meta.fields + ["timeline_events", "related_findings"]


class TimelineSerializer(ScopedSerializer):
    class Meta:
        model = TimelineEvent
        fields = [
            "id",
            "case",
            "artifact",
            "observed_at",
            "timestamp_original",
            "timestamp_format",
            "timestamp_zone",
            "timestamp_meaning",
            "timestamp_precision",
            "timestamp_uncertainty",
            "event_type",
            "summary",
            "interpretation_status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProvenanceSerializer(ScopedSerializer):
    class Meta:
        model = ProvenanceLink
        fields = [
            "id",
            "case",
            "source_evidence",
            "artifact",
            "relationship",
            "rationale",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class FindingSupportSerializer(ScopedSerializer):
    class Meta:
        model = FindingSupport
        fields = ["id", "finding", "artifact", "timeline_event", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        if attrs.get("finding") and attrs["finding"].examiner_status != "draft":
            raise serializers.ValidationError(
                "Submitted support is frozen; supersede the revision first."
            )
        if not attrs.get("artifact") and not attrs.get("timeline_event"):
            raise serializers.ValidationError("Attach an artifact or timeline event.")
        if attrs.get("artifact") and attrs.get("timeline_event"):
            raise serializers.ValidationError("Attach one support source per relationship.")
        return super().validate(attrs)


class FindingSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        forbidden = {
            "examiner_status",
            "review_status",
            "reviewer_comments",
            "reviewed_at",
            "author",
        }
        if self.instance:
            forbidden.add("case")
        if forbidden.intersection(self.initial_data):
            raise serializers.ValidationError("Case and review state require controlled actions.")
        return attrs

    version = serializers.IntegerField(read_only=True)
    revisions = serializers.SerializerMethodField()
    integrity_impact = serializers.SerializerMethodField()

    def get_revisions(self, obj) -> list:
        return [
            {
                "id": str(r.pk),
                "number": r.number,
                "snapshot": r.snapshot,
                "snapshot_hash": r.snapshot_hash,
                "status": r.status,
                "author": str(r.author_id),
                "created_at": r.created_at,
                "decisions": [
                    {
                        "actor": str(d.actor_id),
                        "decision": d.decision,
                        "comments": d.comments,
                        "created_at": d.created_at,
                    }
                    for d in r.decisions.order_by("created_at", "id")
                ],
            }
            for r in obj.revisions.order_by("number")
        ]

    def get_integrity_impact(self, obj) -> str:
        from investigations.services import support_snapshot

        try:
            support_snapshot(obj)
            return "current_support_valid"
        except serializers.ValidationError:
            return "support_incomplete_or_integrity_failed"

    support_count = serializers.IntegerField(source="supports.count", read_only=True)

    class Meta:
        model = Finding
        fields = [
            "id",
            "case",
            "author",
            "finding_text",
            "finding_basis",
            "examiner_status",
            "review_status",
            "reviewer_comments",
            "reviewed_at",
            "created_at",
            "updated_at",
            "support_count",
            "version",
            "revisions",
            "integrity_impact",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "reviewed_at",
            "support_count",
            "version",
            "revisions",
            "integrity_impact",
        ]


class FindingDetailSerializer(FindingSerializer):
    supports = FindingSupportSerializer(many=True, read_only=True)

    class Meta(FindingSerializer.Meta):
        fields = FindingSerializer.Meta.fields + ["supports"]


class BookmarkSerializer(ScopedSerializer):
    class Meta:
        model = Bookmark
        fields = ["id", "case", "artifact", "created_by", "label", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]


class NoteSerializer(ScopedSerializer):
    class Meta:
        model = InvestigatorNote
        fields = ["id", "case", "artifact", "author", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "author", "created_at", "updated_at"]


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "case", "title", "status", "body", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class ExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportPackage
        fields = ["id", "case", "report", "status", "manifest_hash", "requested_by", "created_at"]
        read_only_fields = [f.name for f in ExportPackage._meta.fields]


class AuditSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.display_name", read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "case",
            "actor",
            "actor_name",
            "action",
            "object_type",
            "object_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = [f.name for f in AuditEvent._meta.fields]
