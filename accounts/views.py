# accounts/views.py

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

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


# ============================================================
# API - REGISTER
# POST /api/accounts/register/
# ============================================================


class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()

    serializer_class = RegisterSerializer

    permission_classes = [permissions.AllowAny]

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        USER_REGISTER_COUNTER.inc()

        log_activity(
            user,
            "register",
            request,
        )

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# API - JWT LOGIN
# POST /api/accounts/login/
# ============================================================


class LoginView(TokenObtainPairView):

    serializer_class = CustomTokenObtainPairSerializer

    permission_classes = [permissions.AllowAny]

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        USER_LOGIN_COUNTER.inc()

        log_activity(
            serializer.user,
            "login",
            request,
        )

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# API - LOGOUT
# POST /api/accounts/logout/
# ============================================================


class LogoutView(APIView):

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

        log_activity(
            request.user,
            "logout",
            request,
        )

        return Response(status=status.HTTP_205_RESET_CONTENT)


# ============================================================
# API - PROFILE
# GET/PATCH /api/accounts/me/
# ============================================================


class MeView(generics.RetrieveUpdateAPIView):

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):

        return self.request.user

    def get_serializer_class(self):

        if self.request.method in [
            "PUT",
            "PATCH",
        ]:

            return ProfileUpdateSerializer

        return UserSerializer

    def perform_update(
        self,
        serializer,
    ):

        user = serializer.save()

        PROFILE_UPDATE_COUNTER.inc()

        log_activity(
            user,
            "profile_update",
            self.request,
        )


# ============================================================
# BROWSER LOGIN
# GET/POST /accounts/login/
# ============================================================


def web_login_view(request):

    if request.user.is_authenticated:

        return redirect("core:dashboard")

    username = ""

    next_url = request.POST.get("next") or request.GET.get("next") or ""

    error_message = ""

    if request.method == "POST":

        username = request.POST.get("username", "").strip()

        password = request.POST.get("password", "")

        if not username or not password:

            error_message = "Username and password are required."

        else:

            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is not None:

                django_login(
                    request,
                    user,
                )

                USER_LOGIN_COUNTER.inc()

                log_activity(
                    user,
                    "login",
                    request,
                )

                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):

                    return redirect(next_url)

                return redirect("core:dashboard")

            error_message = "Invalid username or password."

    return render(
        request,
        "accounts/login.html",
        {
            "username": username,
            "next": next_url,
            "error_message": error_message,
        },
    )


# ============================================================
# BROWSER LOGOUT
# POST /accounts/logout/
# ============================================================


def web_logout_view(request):

    if request.method == "POST":

        if request.user.is_authenticated:

            log_activity(
                request.user,
                "logout",
                request,
            )

            django_logout(request)

    return redirect("accounts:login")
