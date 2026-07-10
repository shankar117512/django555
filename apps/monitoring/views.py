# apps/monitoring/views.py
import datetime

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from orders.models import Client

from .models import ActivityLog
from .serializers import ActivityLogSerializer, DashboardMetricsSerializer

VERSION = "1.0.0"
CACHE_KEY = "health_check_probe"
CACHE_VALUE = "ok"


# ── Public infra health checks (existing, tested code —) ────────


def health_check(request):
    """GET /monitoring/  — full health check (public)."""
    checks = {}
    overall = "healthy"

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "healthy"}
    except Exception as exc:
        checks["database"] = {"status": "unhealthy", "detail": str(exc)}
        overall = "unhealthy"

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
    """GET /monitoring/ping/  — bare liveness probe."""
    return JsonResponse({"status": "ok"})


def db_metrics(request):
    """GET /monitoring/db/  — detailed DB metrics."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"db": "ok"})
    except Exception as exc:
        return JsonResponse({"db": "error", "detail": str(exc)}, status=500)


class ServerMetricsView(APIView):
    """GET /monitoring/server/  — admin-only. 401/403/200."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return Response(None)


# ── Business/dashboard metrics (add) ──────────────────────────


class DashboardMetricsView(APIView):
    """
    GET /monitoring/dashboard/
    Frontend Dashboard page open API call.
    total users, today active users, total clients, recent activity — cards.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        data = {
            "total_users": User.objects.count(),
            "active_users_today": User.objects.filter(last_login__date=today).count(),
            "total_clients": Client.objects.count(),
            "recent_activity": ActivityLog.objects.select_related("user")[:10],
        }
        serializer = DashboardMetricsSerializer(data)
        return Response(serializer.data)


class ActivityLogListView(generics.ListAPIView):
    """GET /monitoring/activity/  — activity history (pagination)."""

    queryset = ActivityLog.objects.select_related("user")
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
