import json
from datetime import datetime
from pathlib import Path

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import AuditEvent
from evidence.models import CustodyEvent, EvidenceHash, EvidenceItem
from evidence.services import verify_evidence
from investigations.models import (
    Artifact,
    Bookmark,
    Finding,
    FindingSupport,
    InvestigatorNote,
    ProvenanceLink,
    TimelineEvent,
)
from processing.models import ProcessingJob
from processing.tasks import process_evidence_job
from reporting.models import ExportPackage, Report

from .models import Case, CaseParticipant
from .permissions import has_case_access
from .serializers import (
    ArtifactDetailSerializer,
    ArtifactSerializer,
    AuditSerializer,
    BookmarkSerializer,
    CaseSerializer,
    CustodySerializer,
    EvidenceDetailSerializer,
    EvidenceSerializer,
    FindingDetailSerializer,
    FindingSerializer,
    FindingSupportSerializer,
    JobSerializer,
    NoteSerializer,
    ParticipantSerializer,
    ProvenanceSerializer,
    ReportSerializer,
    TimelineSerializer,
)


def deny(message="Case access denied.", code="permission_denied"):
    return Response({"detail": message, "code": code}, status=status.HTTP_403_FORBIDDEN)


def case_for(request, case_id, write=False):
    case = get_object_or_404(Case, pk=case_id)
    return case if has_case_access(request.user, case, write) else None


def audit(request, case, action, object_type="", object_id="", metadata=None):
    safe_metadata = metadata or {}
    return AuditEvent.objects.create(
        case=case,
        actor=request.user,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        metadata=safe_metadata,
    )


def json_ready(value):
    return json.loads(json.dumps(value, default=str))


class CaseListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Case.objects.filter(participants__user=request.user) | Case.objects.filter(
            owner=request.user
        )
        return Response(CaseSerializer(queryset.distinct(), many=True).data)

    def post(self, request):
        serializer = CaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            case = serializer.save(owner=request.user)
            CaseParticipant.objects.create(case=case, user=request.user, permission="owner")
            audit(request, case, "case.created", "Case", case.id)
        return Response(CaseSerializer(case).data, status=status.HTTP_201_CREATED)


class CaseDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        case = case_for(request, pk)
        if not case:
            return deny()
        return Response(CaseSerializer(case).data)


class ParticipantList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return Response(ParticipantSerializer(case.participants.all(), many=True).data)

    def post(self, request, case_id):
        case = case_for(request, case_id, write=True)
        if not case:
            return deny("Case write access denied.")
        serializer = ParticipantSerializer(data={**request.data, "case": str(case.id)})
        serializer.is_valid(raise_exception=True)
        participant = serializer.save()
        audit(
            request,
            case,
            "case.participant_added",
            "CaseParticipant",
            participant.id,
            {"permission": participant.permission},
        )
        return Response(ParticipantSerializer(participant).data, status=status.HTTP_201_CREATED)


class EvidenceListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return Response(
            EvidenceSerializer(
                case.evidence_items.select_related("registered_by").all(), many=True
            ).data
        )

    def post(self, request, case_id):
        case = case_for(request, case_id, write=True)
        if not case:
            return deny("Case write access denied.")
        serializer = EvidenceSerializer(data={**request.data, "case": str(case.id)})
        serializer.is_valid(raise_exception=True)
        evidence = serializer.save(registered_by=request.user)
        CustodyEvent.objects.create(
            case=case,
            evidence=evidence,
            actor=request.user,
            action="registered",
            details={"readOnly": evidence.read_only, "synthetic": evidence.is_synthetic},
        )
        audit(
            request,
            case,
            "evidence.registered",
            "EvidenceItem",
            evidence.id,
            {"synthetic": evidence.is_synthetic},
        )
        return Response(EvidenceSerializer(evidence).data, status=status.HTTP_201_CREATED)


class EvidenceDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, evidence_id):
        evidence = get_object_or_404(
            EvidenceItem.objects.select_related("registered_by"), pk=evidence_id
        )
        if not has_case_access(request.user, evidence.case):
            return deny()
        return Response(EvidenceDetailSerializer(evidence).data)


class EvidenceVerify(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, evidence_id):
        evidence = get_object_or_404(EvidenceItem, pk=evidence_id)
        if not has_case_access(request.user, evidence.case):
            return deny()
        return Response(
            {
                "id": str(evidence.id),
                "verification_status": evidence.verification_status,
                "calculated_hash": evidence.calculated_hash,
                "expected_hash": evidence.expected_hash,
                "hash_algorithm": evidence.hash_algorithm,
                "processing_status": EvidenceSerializer(evidence).data["processing_status"],
            }
        )

    def post(self, request, evidence_id):
        evidence = get_object_or_404(EvidenceItem, pk=evidence_id)
        if not has_case_access(request.user, evidence.case, write=True):
            return deny("Case write access denied.")
        try:
            calculated, verification_status = verify_evidence(evidence)
        except OSError:
            calculated, verification_status = "", "unreadable"
        evidence.calculated_hash = calculated
        evidence.verification_status = verification_status
        evidence.save(update_fields=["calculated_hash", "verification_status", "updated_at"])
        if verification_status == "unreadable":
            action = "hash_verification_failed"
            details = {"status": verification_status}
            response = {"detail": "Evidence path is not readable.", "code": "evidence_unreadable"}
            response_status = status.HTTP_400_BAD_REQUEST
        else:
            EvidenceHash.objects.create(evidence=evidence, algorithm="SHA-256", value=calculated)
            action = "hash_verified" if verification_status == "verified" else "hash_mismatch"
            details = {"status": verification_status, "algorithm": "SHA-256"}
            response = EvidenceDetailSerializer(evidence).data
            response_status = status.HTTP_200_OK
        CustodyEvent.objects.create(
            case=evidence.case,
            evidence=evidence,
            actor=request.user,
            action=action,
            details=details,
        )
        audit(request, evidence.case, f"evidence.{action}", "EvidenceItem", evidence.id, details)
        return Response(response, status=response_status)


class JobListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return Response(
            JobSerializer(case.processing_jobs.prefetch_related("runs").all(), many=True).data
        )

    def post(self, request, case_id):
        case = case_for(request, case_id, write=True)
        if not case:
            return deny("Case write access denied.")
        evidence = get_object_or_404(EvidenceItem, pk=request.data.get("evidence"), case=case)
        if evidence.verification_status != "verified":
            audit(
                request,
                case,
                "processing.blocked",
                "EvidenceItem",
                evidence.id,
                {"verification_status": evidence.verification_status},
            )
            return Response(
                {
                    "detail": "Processing is blocked until evidence integrity is verified.",
                    "code": "integrity_required",
                },
                status=status.HTTP_409_CONFLICT,
            )
        job = ProcessingJob.objects.create(case=case, evidence=evidence, requested_by=request.user)
        audit(request, case, "processing.submitted", "ProcessingJob", job.id)
        process_evidence_job.delay(str(job.id))
        job.refresh_from_db()
        return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)


class JobDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = get_object_or_404(ProcessingJob.objects.prefetch_related("runs"), pk=job_id)
        if not has_case_access(request.user, job.case):
            return deny()
        return Response(JobSerializer(job).data)


class ArtifactList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        queryset = case.artifacts.all()
        query = request.query_params.get("q", "").strip().lower()
        if query:
            queryset = [
                artifact
                for artifact in queryset
                if query
                in f"{artifact.source_path} {artifact.artifact_type} {artifact.content}".lower()
            ]
        return Response(ArtifactSerializer(queryset, many=True).data)


class ArtifactDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, artifact_id):
        artifact = get_object_or_404(
            Artifact.objects.select_related("source_evidence", "processing_run"), pk=artifact_id
        )
        if not has_case_access(request.user, artifact.case):
            return deny()
        return Response(ArtifactDetailSerializer(artifact).data)


class ProvenanceList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return Response(ProvenanceSerializer(case.provenance_links.all(), many=True).data)


class TimelineList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        queryset = case.timeline_events.all()
        event_type = request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        try:
            if date_from:
                queryset = queryset.filter(
                    observed_at__gte=datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                )
            if date_to:
                queryset = queryset.filter(
                    observed_at__lte=datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                )
        except ValueError:
            return Response(
                {"detail": "Date filters must be ISO-8601 values.", "code": "invalid_date_filter"},
                status=400,
            )
        return Response(TimelineSerializer(queryset, many=True).data)


class ArtifactProvenance(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, artifact_id):
        artifact = get_object_or_404(
            Artifact.objects.select_related("source_evidence", "processing_run"), pk=artifact_id
        )
        if not has_case_access(request.user, artifact.case):
            return deny()
        links = ProvenanceLink.objects.filter(artifact=artifact)
        return Response(
            {
                "artifact": ArtifactSerializer(artifact).data,
                "processing_run": {
                    "id": str(artifact.processing_run.id),
                    "processor_name": artifact.processing_run.processor_name,
                    "processor_version": artifact.processing_run.processor_version,
                    "status": artifact.processing_run.status,
                },
                "original_evidence": EvidenceDetailSerializer(artifact.source_evidence).data,
                "provenance_links": ProvenanceSerializer(links, many=True).data,
                "timeline_events": TimelineSerializer(
                    artifact.timeline_events.all(), many=True
                ).data,
                "related_findings": FindingSerializer(
                    Finding.objects.filter(supports__artifact=artifact).distinct(), many=True
                ).data,
            }
        )


class FindingListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return Response(
            FindingDetailSerializer(
                case.findings.prefetch_related("supports").all(), many=True
            ).data
        )

    def post(self, request, case_id):
        case = case_for(request, case_id, write=True)
        if not case:
            return deny("Case write access denied.")
        serializer = FindingSerializer(data={**request.data, "case": str(case.id)})
        serializer.is_valid(raise_exception=True)
        finding = serializer.save(author=request.user, examiner_status="draft")
        audit(
            request,
            case,
            "finding.created",
            "Finding",
            finding.id,
            {"finding_basis": finding.finding_basis},
        )
        return Response(FindingDetailSerializer(finding).data, status=status.HTTP_201_CREATED)


class FindingDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, finding_id):
        finding = get_object_or_404(Finding.objects.prefetch_related("supports"), pk=finding_id)
        if not has_case_access(request.user, finding.case):
            return deny()
        return Response(FindingDetailSerializer(finding).data)

    def patch(self, request, finding_id):
        finding = get_object_or_404(Finding, pk=finding_id)
        if not has_case_access(request.user, finding.case, write=True):
            return deny("Case write access denied.")
        serializer = FindingSerializer(finding, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        audit(
            request,
            finding.case,
            "finding.updated",
            "Finding",
            finding.id,
            {"fields": list(request.data.keys())},
        )
        return Response(FindingDetailSerializer(updated).data)


class FindingSupportListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, finding_id):
        finding = get_object_or_404(Finding, pk=finding_id)
        if not has_case_access(request.user, finding.case):
            return deny()
        return Response(FindingSupportSerializer(finding.supports.all(), many=True).data)

    def post(self, request, finding_id):
        finding = get_object_or_404(Finding, pk=finding_id)
        if not has_case_access(request.user, finding.case, write=True):
            return deny("Case write access denied.")
        data = {**request.data, "finding": str(finding.id)}
        serializer = FindingSupportSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        support = serializer.save()
        if support.artifact_id and support.artifact.case_id != finding.case_id:
            support.delete()
            return Response(
                {
                    "detail": "Support artifact must belong to the finding case.",
                    "code": "case_mismatch",
                },
                status=400,
            )
        if support.timeline_event_id and support.timeline_event.case_id != finding.case_id:
            support.delete()
            return Response(
                {
                    "detail": "Support timeline event must belong to the finding case.",
                    "code": "case_mismatch",
                },
                status=400,
            )
        audit(
            request,
            finding.case,
            "finding.support_attached",
            "FindingSupport",
            support.id,
            {
                "artifact": bool(support.artifact_id),
                "timeline_event": bool(support.timeline_event_id),
            },
        )
        return Response(FindingSupportSerializer(support).data, status=status.HTTP_201_CREATED)


class ReportListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return Response(ReportSerializer(case.reports.all(), many=True).data)

    def post(self, request, case_id):
        case = case_for(request, case_id, write=True)
        if not case:
            return deny("Case write access denied.")
        findings = list(case.findings.prefetch_related("supports").all())
        evidence = list(case.evidence_items.all())
        artifacts = list(case.artifacts.all())
        body = {
            "draftNotice": "Development draft. Not court-ready and not forensically validated.",
            "syntheticDataWarning": "Synthetic-data warning: this case may contain synthetic fixtures.",
            "case": {"reference": case.reference, "title": case.title},
            "evidenceRegister": json_ready(EvidenceSerializer(evidence, many=True).data),
            "integrityStatus": {
                "verified": sum(item.verification_status == "verified" for item in evidence),
                "mismatch": sum(item.verification_status == "mismatch" for item in evidence),
                "unreadable": sum(item.verification_status == "unreadable" for item in evidence),
            },
            "processingSummary": {
                "artifacts": len(artifacts),
                "jobs": case.processing_jobs.count(),
            },
            "findings": json_ready(FindingDetailSerializer(findings, many=True).data),
            "supportingArtifacts": [
                str(support.artifact_id)
                for finding in findings
                for support in finding.supports.all()
                if support.artifact_id
            ],
            "provenanceReferences": json_ready(
                ProvenanceSerializer(case.provenance_links.all(), many=True).data
            ),
            "timelineReferences": json_ready(
                TimelineSerializer(case.timeline_events.all(), many=True).data
            ),
            "auditSummary": {"events": case.audit_events.count()},
            "limitations": sorted(
                {limitation for artifact in artifacts for limitation in artifact.limitations}
            ),
            "status": "draft",
        }
        report = Report.objects.create(
            case=case,
            title=request.data.get("title", f"Draft report: {case.reference}"),
            body=body,
            created_by=request.user,
        )
        audit(
            request,
            case,
            "report.draft_generated",
            "Report",
            report.id,
            {"status": "draft", "finding_count": len(findings)},
        )
        return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)


class ReportDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, report_id):
        report = get_object_or_404(Report, pk=report_id)
        if not has_case_access(request.user, report.case):
            return deny()
        return Response(ReportSerializer(report).data)


class AuditList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return Response(
            AuditSerializer(case.audit_events.select_related("actor").all(), many=True).data
        )


class GlobalAuditList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = AuditEvent.objects.filter(actor=request.user, case__isnull=True).select_related(
            "actor"
        )
        return Response(AuditSerializer(events, many=True).data)


class BookmarkListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return Response(BookmarkSerializer(case.bookmarks.all(), many=True).data)

    def post(self, request, case_id):
        case = case_for(request, case_id, write=True)
        if not case:
            return deny("Case write access denied.")
        serializer = BookmarkSerializer(data={**request.data, "case": str(case.id)})
        serializer.is_valid(raise_exception=True)
        bookmark = serializer.save(created_by=request.user)
        audit(request, case, "bookmark.created", "Bookmark", bookmark.id)
        return Response(BookmarkSerializer(bookmark).data, status=201)


class NoteListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return Response(NoteSerializer(case.notes.all(), many=True).data)

    def post(self, request, case_id):
        case = case_for(request, case_id, write=True)
        if not case:
            return deny("Case write access denied.")
        serializer = NoteSerializer(data={**request.data, "case": str(case.id)})
        serializer.is_valid(raise_exception=True)
        note = serializer.save(author=request.user)
        audit(request, case, "note.created", "InvestigatorNote", note.id)
        return Response(NoteSerializer(note).data, status=201)


class ExportCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, case_id):
        case = case_for(request, case_id, write=True)
        if not case:
            return deny("Case write access denied.")
        package = ExportPackage.objects.create(
            case=case, requested_by=request.user, status="placeholder"
        )
        audit(request, case, "export.requested", "ExportPackage", package.id)
        return Response(
            {
                "id": str(package.id),
                "status": package.status,
                "message": "Controlled export placeholder; no file was emitted.",
            },
            status=status.HTTP_202_ACCEPTED,
        )
