from django.urls import path
from .views import (
    CaseListCreate,
    CaseDetail,
    EvidenceListCreate,
    EvidenceVerify,
    JobListCreate,
    ArtifactList,
    ProvenanceList,
    FindingListCreate,
    FindingSupportCreate,
    ReportListCreate,
    AuditList,
    ExportCreate,
)

urlpatterns = [
    path("cases/", CaseListCreate.as_view()),
    path("cases/<uuid:pk>/", CaseDetail.as_view()),
    path("cases/<uuid:case_id>/evidence/", EvidenceListCreate.as_view()),
    path("evidence/<uuid:evidence_id>/verify/", EvidenceVerify.as_view()),
    path("cases/<uuid:case_id>/jobs/", JobListCreate.as_view()),
    path("cases/<uuid:case_id>/artifacts/", ArtifactList.as_view()),
    path("cases/<uuid:case_id>/provenance/", ProvenanceList.as_view()),
    path("cases/<uuid:case_id>/findings/", FindingListCreate.as_view()),
    path("findings/<uuid:finding_id>/support/", FindingSupportCreate.as_view()),
    path("cases/<uuid:case_id>/reports/", ReportListCreate.as_view()),
    path("cases/<uuid:case_id>/audit/", AuditList.as_view()),
    path("cases/<uuid:case_id>/exports/", ExportCreate.as_view()),
]
