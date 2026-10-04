import json
from datetime import datetime
from pathlib import Path

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from audit.models import AuditEvent
from evidence.models import CustodyEvent, EvidenceHash, EvidenceItem
from evidence.services import observe, accept_baseline
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
from .permissions import has_case_access, allowed
from .serializers import (
    ArtifactDetailSerializer,
    ArtifactSerializer,
    AuditSerializer,
    BookmarkSerializer,
    CaseSerializer,
    CustodySerializer,
    EvidenceDetailSerializer,
    EvidenceSerializer,
    ExportSerializer,
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


def case_for(request, case_id, write=False, action=None):
    case = get_object_or_404(Case, pk=case_id)
    return case if allowed(request.user, case, action or ("finding" if write else "read")) else None


def audit(request, case, action, object_type="", object_id="", metadata=None):
    from audit.services import append_event

    return append_event(case, request.user, action, object_type, object_id, metadata)


def json_ready(value):
    return json.loads(json.dumps(value, default=str))


def page_response(request, queryset, serializer, ordering=("created_at", "id")):
    """Bounded, stable offset page used by every collection endpoint."""
    try:
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
    except (TypeError, ValueError):
        return Response({"detail": "limit and offset must be integers"}, status=400)
    if limit < 1 or limit > 100 or offset < 0 or offset > 1_000_000:
        return Response({"detail": "limit must be 1..100 and offset 0..1000000"}, status=400)
    queryset = queryset.order_by(*ordering)
    count = queryset.count()
    return Response(
        {
            "count": count,
            "limit": limit,
            "offset": offset,
            "results": serializer(queryset[offset : offset + limit], many=True).data,
        }
    )


@extend_schema_view(
    get=extend_schema(operation_id="v1_case_list"),
    post=extend_schema(operation_id="v1_case_create"),
)
class CaseListCreate(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer

    def get(self, request):
        queryset = Case.objects.filter(participants__user=request.user) | Case.objects.filter(
            owner=request.user
        )
        return page_response(request, queryset.distinct(), CaseSerializer, ("-created_at", "id"))

    def post(self, request):
        if not allowed(request.user, action="create"):
            return deny("Account cannot create cases.")
        serializer = CaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            case = serializer.save(owner=request.user)
            CaseParticipant.objects.create(case=case, user=request.user, permission="owner")
            audit(request, case, "case.created", "Case", case.id)
        return Response(CaseSerializer(case).data, status=status.HTTP_201_CREATED)


@extend_schema_view(get=extend_schema(operation_id="v1_case_retrieve"))
class CaseDetail(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaseSerializer

    def get(self, request, pk):
        case = case_for(request, pk)
        if not case:
            return deny()
        return Response(
            {
                **CaseSerializer(case).data,
                "actions": {
                    action: allowed(request.user, case, action)
                    for action in (
                        "evidence",
                        "process",
                        "finding",
                        "review",
                        "report",
                        "export",
                        "participants",
                    )
                },
            }
        )


class ParticipantList(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ParticipantSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return page_response(request, case.participants.all(), ParticipantSerializer)

    @transaction.atomic
    def post(self, request, case_id):
        case = case_for(request, case_id, action="participants")
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
    serializer_class = EvidenceSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return page_response(
            request,
            case.evidence_items.select_related("registered_by").all(),
            EvidenceSerializer,
            ("registered_at", "id"),
        )

    @transaction.atomic
    def post(self, request, case_id):
        case = case_for(request, case_id, action="evidence")
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
    serializer_class = EvidenceDetailSerializer

    def get(self, request, evidence_id):
        evidence = get_object_or_404(
            EvidenceItem.objects.select_related("registered_by"), pk=evidence_id
        )
        if not has_case_access(request.user, evidence.case):
            return deny()
        return Response(EvidenceDetailSerializer(evidence).data)


class EvidenceVerify(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EvidenceDetailSerializer

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
        if not allowed(request.user, evidence.case, "evidence"):
            return deny("Evidence verification denied.")
        observe(evidence, request.user)
        return Response(
            EvidenceDetailSerializer(evidence).data,
            status=400 if evidence.verification_status == "unreadable" else 200,
        )


class EvidenceAcceptBaseline(APIView):
    serializer_class = EvidenceDetailSerializer

    def post(self, request, evidence_id):
        evidence = get_object_or_404(EvidenceItem, pk=evidence_id)
        if not allowed(request.user, evidence.case, "evidence"):
            return deny("Evidence baseline acceptance denied.")
        accept_baseline(evidence, request.user, request.data.get("reason"))
        return Response(EvidenceDetailSerializer(evidence).data)


class JobListCreate(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return page_response(
            request,
            case.processing_jobs.prefetch_related("runs").all(),
            JobSerializer,
        )

    def post(self, request, case_id):
        case = case_for(request, case_id, action="process")
        if not case:
            return deny("Case write access denied.")
        evidence = get_object_or_404(EvidenceItem, pk=request.data.get("evidence"), case=case)
        if (
            evidence.verification_status not in {"verified", "baseline_accepted"}
            or not evidence.baseline_hash
        ):
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
        from processing.services import submit

        prior = None
        if request.data.get("prior_job"):
            prior = get_object_or_404(ProcessingJob, pk=request.data["prior_job"], case=case)
        job = submit(
            evidence,
            request.user,
            request.data.get("parameters"),
            prior,
            request.data.get("reason", ""),
            request.data.get("request_key"),
        )
        job.refresh_from_db()
        return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)


class JobDetail(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer

    def get(self, request, job_id):
        job = get_object_or_404(ProcessingJob.objects.prefetch_related("runs"), pk=job_id)
        if not has_case_access(request.user, job.case):
            return deny()
        return Response(JobSerializer(job).data)


class ArtifactList(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ArtifactSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        queryset = case.artifacts.all()
        query = request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(source_path__icontains=query)
                | Q(artifact_type__icontains=query)
                | Q(content__icontains=query)
            )
        return page_response(request, queryset, ArtifactSerializer)


class ArtifactDetail(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ArtifactDetailSerializer

    def get(self, request, artifact_id):
        artifact = get_object_or_404(
            Artifact.objects.select_related("source_evidence", "processing_run"), pk=artifact_id
        )
        if not has_case_access(request.user, artifact.case):
            return deny()
        if (
            artifact.source_evidence.case_id != artifact.case_id
            or artifact.processing_run.case_id != artifact.case_id
            or artifact.processing_run.job.evidence_id != artifact.source_evidence_id
        ):
            return deny("Broken case provenance boundary.")
        return Response(ArtifactDetailSerializer(artifact).data)


class ProvenanceList(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProvenanceSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return page_response(request, case.provenance_links.all(), ProvenanceSerializer)


class TimelineList(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TimelineSerializer

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
        return page_response(
            request, queryset, TimelineSerializer, ("observed_at", "created_at", "id")
        )


class ArtifactProvenance(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ArtifactDetailSerializer

    def get(self, request, artifact_id):
        artifact = get_object_or_404(
            Artifact.objects.select_related("source_evidence", "processing_run"), pk=artifact_id
        )
        if not has_case_access(request.user, artifact.case):
            return deny()
        if (
            artifact.source_evidence.case_id != artifact.case_id
            or artifact.processing_run.case_id != artifact.case_id
            or artifact.processing_run.job.evidence_id != artifact.source_evidence_id
        ):
            return deny("Broken case provenance boundary.")
        links = ProvenanceLink.objects.filter(
            artifact=artifact, case=artifact.case, source_evidence=artifact.source_evidence
        )
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
                    artifact.timeline_events.filter(case=artifact.case), many=True
                ).data,
                "related_findings": FindingSerializer(
                    Finding.objects.filter(
                        supports__artifact=artifact, case=artifact.case
                    ).distinct(),
                    many=True,
                ).data,
            }
        )


class FindingListCreate(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FindingDetailSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return page_response(
            request,
            case.findings.prefetch_related("supports").all(),
            FindingDetailSerializer,
        )

    @transaction.atomic
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
    serializer_class = FindingDetailSerializer

    def get(self, request, finding_id):
        finding = get_object_or_404(Finding.objects.prefetch_related("supports"), pk=finding_id)
        if not has_case_access(request.user, finding.case):
            return deny()
        return Response(FindingDetailSerializer(finding).data)

    @transaction.atomic
    def patch(self, request, finding_id):
        from investigations.services import Conflict

        finding = get_object_or_404(Finding.objects.select_for_update(), pk=finding_id)
        if (
            not allowed(request.user, finding.case, "finding")
            or finding.author_id != request.user.pk
        ):
            return deny("Finding author access required.")
        serializer = FindingSerializer(finding, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if finding.examiner_status != "draft" or request.data.get("version") != finding.version:
            raise Conflict()
        updated = serializer.save(version=finding.version + 1)
        audit(
            request,
            finding.case,
            "finding.updated",
            "Finding",
            finding.pk,
            {"version": updated.version},
        )
        return Response(FindingDetailSerializer(updated).data)


class FindingSupportListCreate(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FindingSupportSerializer

    def get(self, request, finding_id):
        finding = get_object_or_404(Finding, pk=finding_id)
        if not has_case_access(request.user, finding.case):
            return deny()
        return page_response(request, finding.supports.all(), FindingSupportSerializer)

    @transaction.atomic
    def post(self, request, finding_id):
        finding = get_object_or_404(Finding.objects.select_for_update(), pk=finding_id)
        if not has_case_access(request.user, finding.case, write=True):
            return deny("Case write access denied.")
        data = {**request.data, "finding": str(finding.id)}
        serializer = FindingSupportSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        support = serializer.save()
        finding.version += 1
        finding.save(update_fields=["version"])
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
    serializer_class = ReportSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return page_response(request, case.reports.all(), ReportSerializer, ("-created_at", "id"))

    @transaction.atomic
    def post(self, request, case_id):
        case = case_for(request, case_id, action="report")
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
            "approvedRevisions": [
                {
                    "finding": str(f.pk),
                    "revision": str(r.pk),
                    "snapshot_hash": r.snapshot_hash,
                    "snapshot": r.snapshot,
                }
                for f in findings
                if f.examiner_status == "approved"
                for r in f.revisions.filter(status="approved").order_by("-number")[:1]
            ],
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
    serializer_class = ReportSerializer

    def get(self, request, report_id):
        report = get_object_or_404(Report, pk=report_id)
        if not has_case_access(request.user, report.case):
            return deny()
        return Response(ReportSerializer(report).data)


class AuditList(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AuditSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return page_response(
            request,
            case.audit_events.select_related("actor").all(),
            AuditSerializer,
            ("-created_at", "-id"),
        )


class GlobalAuditList(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AuditSerializer

    def get(self, request):
        events = AuditEvent.objects.filter(actor=request.user, case__isnull=True).select_related(
            "actor"
        )
        return page_response(request, events, AuditSerializer, ("-created_at", "-id"))


class BookmarkListCreate(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookmarkSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return page_response(request, case.bookmarks.all(), BookmarkSerializer)

    @transaction.atomic
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
    serializer_class = NoteSerializer

    def get(self, request, case_id):
        case = case_for(request, case_id)
        if not case:
            return deny()
        return page_response(request, case.notes.all(), NoteSerializer)

    @transaction.atomic
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
    serializer_class = ExportSerializer

    def post(self, request, case_id):
        case = case_for(request, case_id, action="export")
        if not case:
            return deny("Case write access denied.")
        from reporting.services import create_package
        from reporting.views import package_status

        report = None
        if request.data.get("report"):
            report = get_object_or_404(Report, pk=request.data["report"], case=case)
        package = create_package(case, request.user, report)
        return Response(package_status(package), status=201)
