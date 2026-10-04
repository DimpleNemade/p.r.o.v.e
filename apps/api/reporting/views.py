from pathlib import Path
from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from cases.permissions import allowed
from cases.serializers import ExportSerializer
from audit.services import append_event
from .models import ExportPackage


def package_status(package):
    return {
        "id": str(package.pk),
        "status": package.status,
        "content_digest": package.content_digest,
        "manifest_hash": package.manifest_hash,
        "error": package.error,
        "download_url": f"/api/v1/exports/{package.pk}/download/"
        if package.status == "ready"
        else None,
    }


class ExportStatus(APIView):
    serializer_class = ExportSerializer

    def get(self, request, package_id):
        package = get_object_or_404(ExportPackage, pk=package_id)
        if not allowed(request.user, package.case, "export"):
            raise PermissionDenied("Current export permission required")
        return Response(package_status(package))


class ExportDownload(APIView):
    serializer_class = ExportSerializer

    def get(self, request, package_id):
        package = get_object_or_404(ExportPackage, pk=package_id)
        if not allowed(request.user, package.case, "export"):
            raise PermissionDenied("Current export permission required")
        if package.status != "ready" or package.storage_name != f"{package.pk}.zip":
            raise ValidationError("Package is not ready")
        path = Path(settings.OUTPUT_ROOT) / "exports" / package.storage_name
        handle = path.open("rb")
        append_event(
            package.case,
            request.user,
            "export.downloaded",
            "ExportPackage",
            package.pk,
            {"content_digest": package.content_digest},
        )
        return FileResponse(
            handle,
            as_attachment=True,
            filename=f"prove-{package.pk}.zip",
            content_type="application/zip",
        )
