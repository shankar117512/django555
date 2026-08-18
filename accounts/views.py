# accounts/views.py

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.messages import error as message_error
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
# API VIEWS
# Existing API URLs remain unchanged:
#
# /api/accounts/register/
# /api/accounts/login/
# /api/accounts/logout/
# /api/accounts/me/
# /api/accounts/token/refresh/
# ============================================================


class RegisterView(generics.CreateAPIView):
    """
    POST /api/accounts/register/
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):

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


class LoginView(TokenObtainPairView):
    """
    POST /api/accounts/login/

    Returns:
        access
        refresh
        user
    """

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

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


class LogoutView(APIView):
    """
    POST /api/accounts/logout/

    Body:
        {
            "refresh": "<refresh_token>"
        }
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):

        refresh_token = request.data.get(
            "refresh"
        )

        if not refresh_token:

            return Response(
                {
                    "detail":
                    "refresh token is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            RefreshToken(
                refresh_token
            ).blacklist()

        except TokenError:

            return Response(
                {
                    "detail":
                    "invalid or expired token"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_activity(
            request.user,
            "logout",
            request,
        )

        return Response(
            status=status.HTTP_205_RESET_CONTENT
        )


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET/PATCH /api/accounts/me/
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_object(self):

        return self.request.user

    def get_serializer_class(self):

        if self.request.method in [
            "PUT",
            "PATCH",
        ]:

            return ProfileUpdateSerializer

        return UserSerializer

    def perform_update(self, serializer):

        user = serializer.save()

        PROFILE_UPDATE_COUNTER.inc()

        log_activity(
            user,
            "profile_update",
            self.request,
        )


# ============================================================
# WEB / SESSION LOGIN
#
# /accounts/login/
# /accounts/logout/
#
# These are NOT JWT API endpoints.
# ============================================================


def web_login_view(request):
    """
    Browser login page.

    GET:
        Show login page.

    POST:
        Authenticate user using Django session authentication.
    """

    if request.user.is_authenticated:

        return redirect(
            "core:dashboard"
        )

    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or ""
    )

    if request.method == "POST":

        form = AuthenticationForm(
            request,
            data=request.POST,
        )

        if form.is_valid():

            user = form.get_user()

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

            if (
                next_url
                and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={
                        request.get_host()
                    },
                    require_https=request.is_secure(),
                )
            ):

                return redirect(
                    next_url
                )

            return redirect(
                "core:dashboard"
            )

        message_error(
            request,
            "Invalid username or password.",
        )

    else:

        form = AuthenticationForm(
            request
        )

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


def web_logout_view(request):
    """
    Browser logout.

    POST only.
    """

    if request.method != "POST":

        return redirect(
            "accounts:login"
        )

    if request.user.is_authenticated:

        log_activity(
            request.user,
            "logout",
            request,
        )

        django_logout(
            request
        )

    return redirect(
        "accounts:login"
    )
