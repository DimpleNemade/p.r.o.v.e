import hashlib
import os
from pathlib import Path
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Case, CaseParticipant
from .permissions import has_case_access
from .serializers import *
from evidence.models import EvidenceItem, EvidenceHash, CustodyEvent
from processing.models import ProcessingJob
from processing.tasks import process_evidence_job
from investigations.models import Artifact, TimelineEvent, ProvenanceLink, Finding, FindingSupport
from reporting.models import Report, ExportPackage
from audit.models import AuditEvent


def audit(request, case, action, object_type="", object_id="", metadata=None):
    return AuditEvent.objects.create(
        case=case,
        actor=request.user,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        metadata=metadata or {},
    )


class CaseListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Case.objects.filter(participants__user=request.user) | Case.objects.filter(
            owner=request.user
        )
        return Response(CaseSerializer(qs.distinct(), many=True).data)

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

    def get_object(self, request, pk):
        case = Case.objects.get(pk=pk)
        if not has_case_access(request.user, case):
            return None
        return case

    def get(self, request, pk):
        case = self.get_object(request, pk)
        if not case:
            return Response({"detail": "Case access denied."}, status=403)
        return Response(CaseSerializer(case).data)


class EvidenceListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case):
            return Response({"detail": "Case access denied."}, status=403)
        return Response(EvidenceSerializer(case.evidence_items.all(), many=True).data)

    def post(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case, True):
            return Response({"detail": "Case write access denied."}, status=403)
        serializer = EvidenceSerializer(data={**request.data, "case": str(case.id)})
        serializer.is_valid(raise_exception=True)
        evidence = serializer.save(registered_by=request.user)
        CustodyEvent.objects.create(
            case=case,
            evidence=evidence,
            actor=request.user,
            action="registered",
            details={"readOnly": evidence.read_only},
        )
        audit(request, case, "evidence.registered", "EvidenceItem", evidence.id)
        return Response(EvidenceSerializer(evidence).data, status=201)


class EvidenceVerify(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, evidence_id):
        evidence = EvidenceItem.objects.get(pk=evidence_id)
        if not has_case_access(request.user, evidence.case, True):
            return Response({"detail": "Case write access denied."}, status=403)
        path = Path(evidence.original_path)
        if not path.is_file():
            evidence.verification_status = "unreadable"
            evidence.save(update_fields=["verification_status", "updated_at"])
            CustodyEvent.objects.create(
                case=evidence.case,
                evidence=evidence,
                actor=request.user,
                action="hash_verification_failed",
                details={"status": "unreadable"},
            )
            audit(
                request,
                evidence.case,
                "evidence.hash_verification_failed",
                "EvidenceItem",
                evidence.id,
                {"status": "unreadable"},
            )
            return Response({"detail": "Evidence path is not readable."}, status=400)
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        evidence.calculated_hash = digest.hexdigest()
        evidence.verification_status = (
            "verified"
            if not evidence.expected_hash
            or evidence.expected_hash.lower() == evidence.calculated_hash
            else "mismatch"
        )
        evidence.save(update_fields=["calculated_hash", "verification_status", "updated_at"])
        EvidenceHash.objects.create(
            evidence=evidence, algorithm="SHA-256", value=evidence.calculated_hash
        )
        CustodyEvent.objects.create(
            case=evidence.case,
            evidence=evidence,
            actor=request.user,
            action="hash_verified",
            details={"status": evidence.verification_status},
        )
        audit(
            request,
            evidence.case,
            "evidence.hash_verified",
            "EvidenceItem",
            evidence.id,
            {"status": evidence.verification_status},
        )
        return Response(EvidenceSerializer(evidence).data)


class JobListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case):
            return Response({"detail": "Case access denied."}, status=403)
        return Response(JobSerializer(case.processing_jobs.all(), many=True).data)

    def post(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        evidence = EvidenceItem.objects.get(pk=request.data.get("evidence"), case=case)
        if not has_case_access(request.user, case, True):
            return Response({"detail": "Case write access denied."}, status=403)
        job = ProcessingJob.objects.create(case=case, evidence=evidence, requested_by=request.user)
        process_evidence_job.delay(str(job.id))
        audit(request, case, "processing.submitted", "ProcessingJob", job.id)
        return Response(JobSerializer(job).data, status=201)


class ArtifactList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case):
            return Response({"detail": "Case access denied."}, status=403)
        qs = case.artifacts.all()
        query = request.query_params.get("q", "").strip().lower()
        if query:
            qs = [a for a in qs if query in (a.source_path + " " + str(a.content)).lower()]
        return Response(ArtifactSerializer(qs, many=True).data)


class ProvenanceList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case):
            return Response({"detail": "Case access denied."}, status=403)
        return Response(ProvenanceSerializer(case.provenance_links.all(), many=True).data)


class FindingListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case):
            return Response({"detail": "Case access denied."}, status=403)
        return Response(FindingSerializer(case.findings.all(), many=True).data)

    def post(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case, True):
            return Response({"detail": "Case write access denied."}, status=403)
        serializer = FindingSerializer(data={**request.data, "case": str(case.id)})
        serializer.is_valid(raise_exception=True)
        finding = serializer.save(author=request.user)
        audit(request, case, "finding.created", "Finding", finding.id)
        return Response(FindingSerializer(finding).data, status=201)


class FindingSupportCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, finding_id):
        finding = Finding.objects.get(pk=finding_id)
        if not has_case_access(request.user, finding.case, True):
            return Response({"detail": "Case write access denied."}, status=403)
        serializer = SupportSerializer(data={**request.data, "finding": str(finding.id)})
        serializer.is_valid(raise_exception=True)
        support = serializer.save()
        audit(request, finding.case, "finding.support_attached", "FindingSupport", support.id)
        return Response(SupportSerializer(support).data, status=201)


class ReportListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case):
            return Response({"detail": "Case access denied."}, status=403)
        return Response(ReportSerializer(case.reports.all(), many=True).data)

    def post(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case, True):
            return Response({"detail": "Case write access denied."}, status=403)
        body = {
            "findings": FindingSerializer(case.findings.all(), many=True).data,
            "provenance": ProvenanceSerializer(case.provenance_links.all(), many=True).data,
            "generatedAt": timezone.now().isoformat(),
        }
        report = Report.objects.create(
            case=case,
            title=request.data.get("title", f"Draft report: {case.reference}"),
            body=body,
            created_by=request.user,
        )
        audit(request, case, "report.draft_generated", "Report", report.id)
        return Response(ReportSerializer(report).data, status=201)


class AuditList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case):
            return Response({"detail": "Case access denied."}, status=403)
        return Response(AuditSerializer(case.audit_events.all(), many=True).data)


class ExportCreate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, case_id):
        case = Case.objects.get(pk=case_id)
        if not has_case_access(request.user, case, True):
            return Response({"detail": "Case write access denied."}, status=403)
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
            status=202,
        )
