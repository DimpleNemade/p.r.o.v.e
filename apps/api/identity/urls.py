import hashlib
import logging
from django.core.cache import cache
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import serializers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer
from django.urls import path
from audit.models import AuditEvent

CsrfResponse = inline_serializer(name="CsrfResponse", fields={"csrfToken": serializers.CharField()})
Credentials = inline_serializer(
    name="Credentials",
    fields={
        "username": serializers.CharField(),
        "password": serializers.CharField(write_only=True),
    },
)
UserResponse = inline_serializer(
    name="AuthenticatedUser",
    fields={
        "id": serializers.UUIDField(),
        "username": serializers.CharField(),
        "displayName": serializers.CharField(),
        "role": serializers.CharField(),
    },
)


@extend_schema(responses=CsrfResponse)
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


@csrf_protect
@extend_schema(request=Credentials, responses=UserResponse)
@api_view(["POST"])
@permission_classes([AllowAny])
def sign_in(request):
    csrf_response = CsrfViewMiddleware(lambda _request: None).process_view(request, None, (), {})
    if csrf_response is not None:
        return Response({"detail": "CSRF validation failed."}, status=403)
    address = request.META.get("REMOTE_ADDR", "unknown")
    bucket = "login:" + hashlib.sha256(address.encode()).hexdigest()
    cache.add(bucket, 0, timeout=300)
    try:
        attempts = cache.incr(bucket)
    except ValueError:
        attempts = 1
        cache.set(bucket, attempts, timeout=300)
    if attempts > 10:
        return Response({"detail": "Too many login attempts; try again later."}, status=429)
    user = authenticate(
        request,
        username=request.data.get("username", ""),
        password=request.data.get("password", ""),
    )
    if not user:
        logging.getLogger("prove.auth").warning(
            "Authentication failed", extra={"address_digest": bucket[6:]}
        )
        return Response({"detail": "Invalid credentials."}, status=400)
    login(request, user)
    AuditEvent.objects.create(
        actor=user,
        action="login",
        object_type="User",
        object_id=str(user.id),
        metadata={"authentication": "session"},
    )
    return Response(
        {"id": str(user.id), "username": user.username, "displayName": str(user), "role": user.role}
    )


@extend_schema(request=None, responses={204: None})
@api_view(["POST"])
def sign_out(request):
    if request.user.is_authenticated:
        AuditEvent.objects.create(
            actor=request.user,
            action="logout",
            object_type="User",
            object_id=str(request.user.id),
            metadata={"authentication": "session"},
        )
    logout(request)
    return Response(status=204)


@extend_schema(responses=UserResponse)
@api_view(["GET"])
def me(request):
    return Response(
        {
            "id": str(request.user.id),
            "username": request.user.username,
            "displayName": str(request.user),
            "role": request.user.role,
        }
    )


urlpatterns = [
    path("csrf/", csrf),
    path("login/", sign_in),
    path("logout/", sign_out),
    path("me/", me),
]
