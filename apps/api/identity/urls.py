from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.urls import path


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


@csrf_protect
@api_view(["POST"])
@permission_classes([AllowAny])
def sign_in(request):
    csrf_response = CsrfViewMiddleware(lambda _request: None).process_view(request, None, (), {})
    if csrf_response is not None:
        return Response({"detail": "CSRF validation failed."}, status=403)
    user = authenticate(
        request,
        username=request.data.get("username", ""),
        password=request.data.get("password", ""),
    )
    if not user:
        return Response({"detail": "Invalid credentials."}, status=400)
    login(request, user)
    return Response(
        {"id": str(user.id), "username": user.username, "displayName": str(user), "role": user.role}
    )


@api_view(["POST"])
def sign_out(request):
    logout(request)
    return Response(status=204)


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
