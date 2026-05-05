# apps/monitoring/views.py
import datetime

import psutil  # noqa: F401
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser


def health_check(request):
    """
    Public endpoint: /health/
    Returns 200 for healthy OR degraded (cache issue).
    Returns 503 ONLY for DB failure.
    """
    checks = {}
    overall_status = "healthy"
    http_status = 200

    # --- Database check (only this can cause 503) ---
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "healthy"}
    except Exception as exc:
        checks["database"] = {"status": "unhealthy", "error": str(exc)}
        overall_status = "unhealthy"
        http_status = 503

    # --- Cache check (degraded = 200, not 503) ---
    try:
        cache.set("health_probe", "ok", timeout=10)
        val = cache.get("health_probe")
        if val == "ok":
            checks["cache"] = {"status": "healthy"}
        else:
            checks["cache"] = {
                "status": "degraded",
                "detail": f"unexpected value: {val!r}",
            }
            if overall_status == "healthy":
                overall_status = "degraded"
                # KEY FIX: degraded cache still returns 200 — don't block deployments
    except Exception as exc:
        checks["cache"] = {"status": "degraded", "error": str(exc)}
        if overall_status == "healthy":
            overall_status = "degraded"

    return JsonResponse(
        {
            "status": overall_status,
            "checks": checks,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "version": "1.0.0",
        },
        status=http_status,
    )


def ping(request):
    """Bare-minimum liveness check — no DB, no cache. Always 200."""
    return JsonResponse({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def server_metrics(request):
    # ... unchanged ...
    pass  # ← add this
