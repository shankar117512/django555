# apps/api/urls.py

from django.urls import include, path

from . import views

app_name = "api"


urlpatterns = [
    path(
        "protected/",
        views.ProtectedView.as_view(),
        name="protected",
    ),
    # ========================================================
    # ACCOUNT API
    # ========================================================
    path(
        "accounts/",
        include(
            ("accounts.urls", "accounts"),
            namespace="accounts",
        ),
    ),
]
