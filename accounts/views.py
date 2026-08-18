# accounts/views.py
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.monitoring.utils import log_activity

from .metrics import (
    PROFILE_UPDATE_COUNTER,
    USER_LOGIN_COUNTER,
    USER_REGISTER_COUNTER,
)
from .serializers import (
    CustomTokenObtainPairSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


# ─────────────────────────────────────────────
# Session-based web login (dashboard కోసం)
# ─────────────────────────────────────────────
class CustomLoginView(LoginView):
    """
    Renders templates/accounts/login.html
    Success అయితే -> /client/dashboard/ కి redirect
    """

    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/client/dashboard/"


def custom_logout(request):
    logout(request)
    return redirect("accounts:login")


# ─────────────────────────────────────────────
# JWT API views (mobile / external clients కోసం)
# ─────────────────────────────────────────────
class RegisterView(generics.CreateAPIView):
    """POST /accounts/api/register/"""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        USER_REGISTER_COUNTER.inc()
        log_activity(user, "register", request)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class APILoginView(TokenObtainPairView):
    """POST /accounts/api/login/  -> {access, refresh, user: {...}}"""

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        USER_LOGIN_COUNTER.inc()
        log_activity(serializer.user, "login", request)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class APILogoutView(APIView):
    """POST /accounts/api/logout/  body: {"refresh": "<refresh_token>"}"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {"detail": "invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        log_activity(request.user, "logout", request)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProfileUpdateSerializer
        return UserSerializer

    def perform_update(self, serializer):
        user = serializer.save()
        PROFILE_UPDATE_COUNTER.inc()
        log_activity(user, "profile_update", self.request)
