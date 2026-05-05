# apps/monitoring/views.py
import datetime

import psutil
from django.core.cache import cache  # module-level — required for conftest mock
from django.db import connection  # module-level — required for conftest mock
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser


def health_check(request):
    """
    Public endpoint: /health/
    Returns 200 (healthy), 503 (unhealthy) or 200 with degraded cache.
    """
    checks = {}
    overall_status = "healthy"
    http_status = 200

    # --- Database check ---
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "healthy"}
    except Exception as exc:
        checks["database"] = {"status": "unhealthy", "error": str(exc)}
        overall_status = "unhealthy"
        http_status = 503

    # --- Cache check ---
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
    except Exception as exc:
        checks["cache"] = {"status": "unhealthy", "error": str(exc)}
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


@api_view(["GET"])
@permission_classes([IsAdminUser])
def server_metrics(request):
    """Admin endpoint: /monitoring/server/"""
    cpu_pct = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    return JsonResponse(
        {
            "cpu": {
                "overall_percent": cpu_pct,
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent": mem.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
            "network": {
                "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def db_metrics(request):
    """Admin endpoint: /monitoring/db/"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM pg_stat_activity")
        active_connections = cursor.fetchone()[0]

        cursor.execute("SELECT pg_database_size(current_database())")
        db_size_bytes = cursor.fetchone()[0]

        cursor.execute("""
            SELECT relname, n_live_tup, n_dead_tup
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            LIMIT 10
            """)
        table_stats = [
            {"table": row[0], "live_rows": row[1], "dead_rows": row[2]}
            for row in cursor.fetchall()
        ]

    return JsonResponse(
        {
            "active_connections": active_connections,
            "db_size_mb": round(db_size_bytes / (1024**2), 2),
            "table_stats": table_stats,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }
    )
