from rest_framework import serializers
from .models import Case, CaseParticipant
from evidence.models import EvidenceItem, CustodyEvent
from processing.models import ProcessingJob
from investigations.models import (
    Artifact,
    TimelineEvent,
    ProvenanceLink,
    Bookmark,
    InvestigatorNote,
    Finding,
    FindingSupport,
)
from reporting.models import Report, ExportPackage
from audit.models import AuditEvent


class CaseSerializer(serializers.ModelSerializer):
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
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseParticipant
        fields = ["id", "case", "user", "permission", "created_at"]
        read_only_fields = ["id", "created_at"]


class EvidenceSerializer(serializers.ModelSerializer):
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
            "registered_by",
            "registered_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "registered_by",
            "registered_at",
            "updated_at",
            "calculated_hash",
            "verification_status",
        ]


class CustodySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustodyEvent
        fields = ["id", "case", "evidence", "action", "actor", "details", "created_at"]
        read_only_fields = ["id", "actor", "created_at"]


class JobSerializer(serializers.ModelSerializer):
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
        ]
        read_only_fields = [
            "id",
            "requested_by",
            "status",
            "error_message",
            "created_at",
            "updated_at",
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


class FindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Finding
        fields = [
            "id",
            "case",
            "author",
            "finding_text",
            "examiner_status",
            "review_status",
            "reviewer_comments",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at", "reviewed_at"]


class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingSupport
        fields = ["id", "finding", "artifact", "timeline_event", "created_at"]
        read_only_fields = ["id", "created_at"]


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "case", "title", "status", "body", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "case",
            "actor",
            "action",
            "object_type",
            "object_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = [f.name for f in AuditEvent._meta.fields]
