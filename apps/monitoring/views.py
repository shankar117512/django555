# apps/monitoring/views.py
import time

import psutil
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db import connections
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    checks = {}
    overall = "ok"

    # --- DB check ---
    try:
        conn = connections["default"]
        conn.cursor()
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
            "checks": checks,
            "timestamp": time.time(),
        },
        status=status_code,
    )


@staff_member_required
@require_GET
def server_metrics(request):
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    disk = psutil.disk_usage("/")
    return JsonResponse(
        {
            "cpu_percent": cpu,
            "memory": {
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            },
        }
    )


@staff_member_required
@require_GET
def db_metrics(request):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE();"
            if "mysql" in connection.vendor
            else (
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = current_schema();"
                if "postgresql" not in connection.vendor
                else "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
            )
        )
        table_count = cursor.fetchone()[0]
    return JsonResponse(
        {
            "vendor": connection.vendor,
            "table_count": table_count,
        }
    )
