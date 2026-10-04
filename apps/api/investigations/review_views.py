from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from cases.serializers import FindingDetailSerializer
from .models import Finding
from .services import transition


class FindingTransition(APIView):
    serializer_class = FindingDetailSerializer

    def post(self, request, finding_id):
        get_object_or_404(Finding, pk=finding_id)
        finding = transition(
            finding_id,
            request.user,
            request.data.get("action"),
            request.data.get("version"),
            request.data.get("comments", ""),
        )
        return Response(FindingDetailSerializer(finding).data)
