# apps/monitoring/views.py
import psutil
from django.core.cache import cache
from django.db import connection
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    checks = {}

    # ✅ DB check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "failed"
        return Response(
            {"status": "error", "checks": checks, "timestamp": now()},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # ✅ Cache check
    try:
        cache.set("health_check", "ok", timeout=1)
        if cache.get("health_check") == "ok":
            checks["cache"] = "ok"
        else:
            checks["cache"] = "degraded"
    except Exception:
        checks["cache"] = "failed"
        return Response(
            {"status": "error", "checks": checks, "timestamp": now()},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response({"status": "ok", "checks": checks, "timestamp": now()})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def server_metrics(request):
    return Response(
        {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
        }
    )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def db_metrics(request):
    return Response({"db": "connected"})
