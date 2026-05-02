# apps/monitoring/views.py
import time

import psutil
from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

# ─── Health Check (already passing — keep as-is) ────────────────────────────


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Public endpoint — returns 200 when healthy, 503 when DB is down.
    """
    result = {"status": "healthy", "database": "ok", "cache": "ok"}
    http_status = status.HTTP_200_OK

    # Database check
    try:
        connection.ensure_connection()
    except Exception:
        result["status"] = "unhealthy"
        result["database"] = "unavailable"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    # Cache check
    try:
        cache.set("health_check_probe", "1", timeout=5)
        if cache.get("health_check_probe") != "1":
            raise ValueError("cache miss")
    except Exception:
        result["cache"] = "degraded"
        if result["status"] == "healthy":
            result["status"] = "degraded"

    return Response(result, status=http_status)


# ─── Server Metrics (admin only) ─────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([IsAdminUser])
def server_metrics(request):
    """
    Returns CPU, memory, and disk usage. Admin-only.
    """
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    data = {
        "cpu": {
            "percent": psutil.cpu_percent(interval=0.1),
            "count": psutil.cpu_count(),
        },
        "memory": {
            "total": vm.total,
            "available": vm.available,
            "used": vm.used,
            "percent": vm.percent,
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        },
        "uptime": time.time() - psutil.boot_time(),
    }
    return Response(data)


# ─── DB Metrics (admin only) ──────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([IsAdminUser])
def db_metrics(request):
    """
    Returns basic database connection stats. Admin-only.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

    data = {
        "database": {
            "vendor": connection.vendor,
            "version": version,
            "queries_logged": len(connection.queries),
        }
    }
    return Response(data)
