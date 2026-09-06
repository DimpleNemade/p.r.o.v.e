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
        fields = ["id", "algorithm", "value", "source", "created_at"]
        read_only_fields = [f.name for f in EvidenceHash._meta.fields]


class EvidenceSerializer(serializers.ModelSerializer):
    processing_status = serializers.SerializerMethodField()
    registered_by_name = serializers.CharField(source="registered_by.display_name", read_only=True)
    synthetic_label = serializers.SerializerMethodField()

    def get_processing_status(self, obj):
        latest = obj.processing_jobs.order_by("-created_at").first()
        return latest.status if latest else "not_started"

    def get_synthetic_label(self, obj):
        return "Synthetic data" if obj.is_synthetic else "Operator-registered evidence"

    class Meta:
        model = EvidenceItem
        fields = [
            "id",
            "case",
            "evidence_type",
            "display_name",
            "original_path",
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
            "started_at",
            "finished_at",
        ]
        read_only_fields = [f.name for f in ProcessingRun._meta.fields]


class JobSerializer(serializers.ModelSerializer):
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
        ]
        read_only_fields = [
            "id",
            "requested_by",
            "status",
            "error_message",
            "created_at",
            "updated_at",
            "runs",
        ]


class ArtifactSerializer(serializers.ModelSerializer):
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

    def get_timeline_events(self, obj):
        return TimelineSerializer(obj.timeline_events.all(), many=True).data

    def get_related_findings(self, obj):
        return FindingSerializer(
            Finding.objects.filter(supports__artifact=obj).distinct(), many=True
        ).data

    class Meta(ArtifactSerializer.Meta):
        fields = ArtifactSerializer.Meta.fields + ["timeline_events", "related_findings"]


class TimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimelineEvent
        fields = [
            "id",
            "case",
            "artifact",
            "observed_at",
            "event_type",
            "summary",
            "interpretation_status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProvenanceSerializer(serializers.ModelSerializer):
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


class FindingSupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingSupport
        fields = ["id", "finding", "artifact", "timeline_event", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        if not attrs.get("artifact") and not attrs.get("timeline_event"):
            raise serializers.ValidationError("Attach an artifact or timeline event.")
        if attrs.get("artifact") and attrs.get("timeline_event"):
            raise serializers.ValidationError("Attach one support source per relationship.")
        return attrs


class FindingSerializer(serializers.ModelSerializer):
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
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "reviewed_at",
            "support_count",
        ]


class FindingDetailSerializer(FindingSerializer):
    supports = FindingSupportSerializer(many=True, read_only=True)

    class Meta(FindingSerializer.Meta):
        fields = FindingSerializer.Meta.fields + ["supports"]


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ["id", "case", "artifact", "created_by", "label", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]


class NoteSerializer(serializers.ModelSerializer):
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
