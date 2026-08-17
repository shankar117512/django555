# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "accounts"

urlpatterns = [
    # ── Web login (session, dashboard కోసం) ──
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.custom_logout, name="logout"),

    # ── JWT API (mobile/external clients కోసం) ──
    path("api/register/", views.RegisterView.as_view(), name="api_register"),
    path("api/login/", views.APILoginView.as_view(), name="api_login"),
    path("api/logout/", views.APILogoutView.as_view(), name="api_logout"),
    path("api/me/", views.MeView.as_view(), name="api_me"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
]
