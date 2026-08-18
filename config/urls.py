"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
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


if settings.DEBUG:

    import debug_toolbar

    urlpatterns = [
        path(
            "__debug__/",
            include(debug_toolbar.urls),
        ),
    ] + urlpatterns
