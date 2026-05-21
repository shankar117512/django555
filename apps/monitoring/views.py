# apps/monitoring/views.py
import datetime

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

VERSION = "1.0.0"
CACHE_KEY = "health_check_probe"
CACHE_VALUE = "ok"


def health_check(request):
    """
    GET /monitoring/  — full health check (public).
    Returns 200 when healthy or degraded, 503 when unhealthy (DB down).
    """
    checks = {}
    overall = "healthy"

    # ── Database ─────────────────────────────────────────────────────────────
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "healthy"}
    except Exception as exc:
        checks["database"] = {"status": "unhealthy", "detail": str(exc)}
        overall = "unhealthy"

    # ── Cache ─────────────────────────────────────────────────────────────────
    try:
        cache.set(CACHE_KEY, CACHE_VALUE, timeout=5)
        retrieved = cache.get(CACHE_KEY)
        if retrieved == CACHE_VALUE:
            checks["cache"] = {"status": "healthy"}
        else:
            checks["cache"] = {"status": "degraded", "detail": "unexpected value"}
            if overall == "healthy":
                overall = "degraded"
    except Exception as exc:
        checks["cache"] = {"status": "degraded", "detail": str(exc)}
        if overall == "healthy":
            overall = "degraded"

    status_code = 503 if overall == "unhealthy" else 200
    payload = {
        "status": overall,
        "version": VERSION,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "checks": checks,
    }
    return JsonResponse(payload, status=status_code)


def ping(request):
    """
    GET /monitoring/ping/  — bare liveness probe (never touches the DB).
    """
    return JsonResponse({"status": "ok"})


def db_metrics(request):
    """
    GET /monitoring/db/  — detailed DB metrics (public).
    Returns 200 with {db: "ok"} or 500 with {db: "error", detail: "..."}.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"db": "ok"})
    except Exception as exc:
        return JsonResponse({"db": "error", "detail": str(exc)}, status=500)


class ServerMetricsView(APIView):
    """
    GET /monitoring/server/  — admin-only server metrics.
    401 for unauthenticated, 403 for non-admin, 200 for admin.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return Response(None)
