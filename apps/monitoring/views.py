# apps/monitoring/views.py
import time

import psutil
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db import connection  # ✅ module-level import so mock_conn patch works
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    checks = {}
    overall = "ok"

    # --- DB check --- uses module-level `connection` so mock_conn works
    try:
        connection.cursor()
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall = "unhealthy"

    # --- Cache check ---
    try:
        cache.set("health_probe", "ok", timeout=5)
        val = cache.get("health_probe")
        if val == "ok":
            checks["cache"] = {"status": "healthy"}
        else:
            checks["cache"] = {"status": "degraded", "detail": "value mismatch"}
            if overall == "ok":
                overall = "degraded"
    except Exception as e:
        checks["cache"] = {"status": "unhealthy", "error": str(e)}
        overall = "unhealthy"

    status_code = 503 if overall == "unhealthy" else 200
    return JsonResponse(
        {
            "status": overall,
            "version": "1.0.0",  # ✅ added: test_health_check_structure expects this
            "checks": checks,  # ✅ already present, now reachable
            "timestamp": time.time(),  # ✅ already present, now reachable
        },
        status=status_code,
    )


@staff_member_required
@require_GET
def server_metrics(request):
    mem = psutil.virtual_memory()
    cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    return JsonResponse(
        {
            # ✅ tests expect: data["cpu"]["overall_percent"]
            "cpu": {
                "overall_percent": psutil.cpu_percent(interval=0.1),
                "per_core": cpu_per_core,
                "count": psutil.cpu_count(),
            },
            # ✅ tests expect: data["memory"]["total_gb"]
            "memory": {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent": mem.percent,
            },
            # ✅ tests expect: data["disk"]["free_gb"]
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
            # ✅ tests expect: data["network"]["bytes_sent_mb"]
            "network": {
                "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
            },
        }
    )


@staff_member_required
@require_GET
def db_metrics(request):
    # uses module-level `connection` import (not a local import anymore)
    with connection.cursor() as cursor:
        # Table count
        if "mysql" in connection.vendor:
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = DATABASE();"
            )
        elif "postgresql" in connection.vendor:
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public';"
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = current_schema();"
            )
        table_count = cursor.fetchone()[0]

        # Active connections (PostgreSQL / MySQL / fallback)
        try:
            if "postgresql" in connection.vendor:
                cursor.execute(
                    "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active';"
                )
            elif "mysql" in connection.vendor:
                cursor.execute("SHOW STATUS LIKE 'Threads_connected';")
            else:
                cursor.execute("SELECT 1;")
            active_connections = cursor.fetchone()[0]
        except Exception:
            active_connections = 0

        # DB size in MB
        try:
            if "postgresql" in connection.vendor:
                cursor.execute(
                    "SELECT pg_database_size(current_database()) / (1024 * 1024.0);"
                )
                db_size_mb = round(cursor.fetchone()[0], 2)
            elif "mysql" in connection.vendor:
                cursor.execute(
                    "SELECT SUM(data_length + index_length) / (1024 * 1024.0) "
                    "FROM information_schema.tables WHERE table_schema = DATABASE();"
                )
                db_size_mb = round(cursor.fetchone()[0] or 0, 2)
            else:
                db_size_mb = 0
        except Exception:
            db_size_mb = 0

    return JsonResponse(
        {
            # ✅ tests expect all four of these keys:
            "active_connections": active_connections,
            "db_size_mb": db_size_mb,
            "table_stats": {
                "vendor": connection.vendor,
                "table_count": table_count,
            },
            "timestamp": time.time(),
        }
    )
