"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views.
"""

# config/urls.py

from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse(
        {"status": "ok"},
        status=200,
    )


urlpatterns = [
    # ========================================================
    # HEALTH
    # ========================================================
    path(
        "health/",
        health_check,
        name="health_check",
    ),

    # ========================================================
    # ADMIN
    # ========================================================
    path(
        "admin/",
        admin.site.urls,
    ),

    # ========================================================
    # CORE / WEB APPLICATION
    # ========================================================
    path(
        "",
        include(
            "apps.core.urls",
            namespace="core",
        ),
    ),

    # ========================================================
    # BROWSER ACCOUNT LOGIN
    #
    # /accounts/login/
    # /accounts/logout/
    # ========================================================
    path(
        "accounts/",
        include(
            ("accounts.web_urls", "accounts"),
            namespace="accounts",
        ),
    ),

    # ========================================================
    # MATCHLINE
    #
    # /matchline/
    # ========================================================
    path(
        "matchline/",
        include(
            ("matchline.urls", "matchline"),
            namespace="matchline",
        ),
    ),

    # ========================================================
    # REST API
    #
    # /api/accounts/...
    # ========================================================
    path(
        "api/",
        include(
            "apps.api.urls",
            namespace="api",
        ),
    ),

    # ========================================================
    # MONITORING
    # ========================================================
    path(
        "monitoring/",
        include(
            "apps.monitoring.urls",
            namespace="monitoring",
        ),
    ),

    # ========================================================
    # PROMETHEUS
    # ========================================================
    path(
        "metrics/",
        include("django_prometheus.urls"),
    ),
]


# ============================================================
# DEBUG TOOLBAR
# ============================================================
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path(
            "__debug__/",
            include(debug_toolbar.urls),
        ),
    ] + urlpatterns
